def get_prompt_for_generating_gsql(graph_name: str, nodes: list[dict], edges: list[dict], task: str, schema_text: str = "",allowed_numeric_text: str = "", relations_text: str = ""): 
    # Format nodes list for readability
    nodes_text =  "(no nodes found)"
    if nodes:
        node_list = []
        for node in nodes:
            # Each node is a dictionary like: {"name": "person", "attributes": {...}}
            name = node.get("name", "UNKNOWN_NODE")
            attr_count = len(node.get("attributes", {}))
            # Show name and how many attributes exist for it
            node_list.append(f"- {name} ({attr_count} attributes )")
        nodes_text = "\n".join(node_list)

  
    # Format edge list (for the LLM prompt)

    edges_text = "(no edges found)"
    if edges:
        edge_list = []
        for edge in edges:
            # Each edge is a dictionary like: {"from": "person", "type": "HAS_USED", "to": "device"}
            from_node = edge.get("from", "UNKNOWN_FROM")
            edge_type = edge.get("type", "UNKNOWN_EDGE")
            to_node = edge.get("to", "UNKNOWN_TO")
            edge_list.append(f"- {from_node} -({edge_type})-> {to_node}")
        edges_text = "\n".join(edge_list)

    prompt = f"""
You are a TigerGraph GSQL assistant. Generate a COMPLETE, READ-ONLY GSQL query.

GRAPH NAME:
{graph_name}

NODE TYPES:
{nodes_text}

EDGE TYPES (directed as shown):
{edges_text}

RELATIONSHIPS (from JSON schema):
{relations_text}


SCHEMA CONTEXT (USE ONLY THESE ATTRIBUTES, DO NOT INVENT):
{schema_text}

ALLOWED NUMERIC ATTRIBUTES (MODEL MUST CHOOSE FROM THESE):
{allowed_numeric_text}

TASK:
{task}

RULES:
- Use TigerGraph GSQL syntax ONLY.
- Use **INTERPRET QUERY**, do NOT use CREATE/RUN/INSTALL QUERY.

- Do NOT generate or include any of the following keywords in the query:
  "DROP", "DELETE", "MODIFY", "CREATE".
  These operations are strictly forbidden because they modify or remove data/schema.

-DO NOT USE:
- NOT EXISTS (not supported in GSQL)
- EXISTS (not supported in GSQL)
- SQL-style subqueries

ADDITIONAL STRICT RULES (MUST FOLLOW):
- Attribute-owner rule: Before using s.<attr> or t.<attr>, verify <attr> exists on that vertex type in SCHEMA CONTEXT. Do NOT invent or assume attribute owners. If an attribute exists only on the opposite vertex, use the opposite prefix (swap s<->t) — but only if the swap matches the schema.
- Reverse-edge rule: If your logical start vertex is the right-hand vertex in the schema, DO NOT traverse the original edge backward. Instead, use an explicitly provided reverse_ edge (e.g., reverse_HAS_USED) that goes from the start type to the other type. If no reverse edge exists, do not invent one — output CANNOT_GENERATE.
- Date / time rule: When filtering by time, use attributes only if present in schema (e.g., e.last_tran or s.last_account_activity_dt); do not invent datetime functions or parameters unless present in schema.
- Safety fallback: If the schema does not contain required attribute or edge information to express the user's task exactly, output exactly this single-line token and nothing else: CANNOT_GENERATE: missing_schema_info
- Single-line & prefix reminder: Output MUST be a single line beginning with: Final GSQL: INTERPRET QUERY () FOR GRAPH <graph_name>. No explanations, no extra text, no code fences.

ABOUT THE JSON CONTEXT:

1. The JSON defines the graph:
   - "vertices": list of vertex types
   - "edges": list of edge types
   - Each vertex has: vertex_name, primary_id, attributes[] (name + type)
   - Each edge has: edge_name, from, to, attributes{{}} (name + type)

2. VERTEX USAGE:
   - The model must use ONLY the attributes listed under each vertex_name.
   - Attribute must match exactly (case-sensitive).
   - If NLP refers to an attribute, apply it to the correct alias:
        s.<attr> if attr belongs to FROM vertex
        t.<attr> if attr belongs to TO vertex

3. EDGE USAGE:
   - GSQL traversal MUST follow:
        <FROM>:s -(edge:e)-> <TO>:t
   - The "from" and "to" in JSON define direction.
   - If query needs the opposite direction, use the reverse_<edge_name> provided in JSON.
   - If no reverse edge exists, output:
        CANNOT_GENERATE: missing_schema_info

4. START SET RULE:
   - Start vertex MUST match the FROM side of the chosen traversal:
        start = {{<FROM_TYPE>.*}};

5. ATTRIBUTE MATCHING:
   - The model must check owner of each attribute:
        - person: fraud, mule, victim, age, bad_bene_count, ...
        - device: devicetype, total, mule_ratio, ...
        - accountnumber: TOTAL_SENT_VALUE, pagerank, ...
   - Never use t.<attr> if <attr> belongs only to s vertex, and vice-versa.

6. NO INVENTION RULE:
   - Do NOT invent new vertex types, edge types, or attributes.
   - Use only names present in the JSON schema.



-Few-Shot Prompting EXAMPLES:
  example:  NL: Show me devices that were never used by any person.
            GSQL: Final GSQL: INTERPRET QUERY () FOR GRAPH Graph_new {{SumAccum<INT> @userCount; start = {{device.*}}; with_users = SELECT s FROM start:s -(reverse_HAS_USED:e)-> person:t ACCUM s.@userCount += 1; unused = SELECT s FROM start:s WHERE s.@userCount == 0; PRINT unused;}}

  example:  NL: List all accountnumber with TOTAL_SENT_VALUE > 10000
             GSQL: Final GSQL: INTERPRET QUERY () FOR GRAPH Graph_new {{ start = {{accountnumber.*}}; result = SELECT s FROM start:s WHERE s.TOTAL_SENT_VALUE > 10000; PRINT result; }}

  example:  NL: Sum totalvalue of outgoing payments per account
            GSQL: Final GSQL: INTERPRET QUERY () FOR GRAPH Graph_new {{ SumAccum<DOUBLE> @totalValue; start = {{accountnumber.*}}; result = SELECT t FROM start:s-(HAS_PAID:e)->accountnumber:t ACCUM @totalValue += e.totalvalue; PRINT @totalValue; }}


- Use ONLY attributes that appear in the above CONTEXT. Do NOT invent attribute names (e.g., do NOT use "amount" unless present).
- WHEN summing, choose the attribute ONLY from the "ALLOWED NUMERIC ATTRIBUTES" list above.
- IF the edge has a numeric attribute, use e.<attribute_name> (from CONTEXT). If the target vertex has the numeric attribute, use t.<attribute_name> (from CONTEXT).
- Use ONLY the provided nodes and edges.
- EDGE DIRECTION RULE:
  Always follow the direction of edges exactly as defined in the provided schema context.
  If an edge is defined in the schema as A -(EDGE)-> B, then traversal MUST be A:s -(EDGE:e)-> B:t.
  Never reverse the direction unless the schema explicitly defines the edge as bidirectional.
  # --- ADD THIS BLOCK TO ENFORCE CORRECT START + ALIASES ---
- TRAVERSAL + START SET RULE:
  The vertex on the LEFT side of the edge in the schema is always alias `s` (source).
  The vertex on the RIGHT side of the edge in the schema is always alias `t` (target).
  Therefore, traversal MUST ALWAYS be:
      <FROM_TYPE>:s -(EDGE:e)-> <TO_TYPE>:t

  The start set MUST match the schema source side:
      start = {{<FROM_TYPE>.*}};

  Do NOT start from <TO_TYPE> when traversing in the schema-defined direction.
# --- END OF ADDED BLOCK ---

# OUTPUT TEMPLATES (Model MUST follow one of these exact shapes)


- Vertex and edge type names are CASE-SENSITIVE. Use exactly the names shown in NODE TYPES / EDGE TYPES / SCHEMA CONTEXT (e.g., "Person" ≠ "person").

- When summing, use ONLY attributes that exist in the provided schema context.
- If the edge has a numeric attribute, use e.<attribute_name> (do not invent new names).
- Query must be READ-ONLY. Do NOT modify the graph.
- DO NOT wrap the output in code fences.
- Output must START with exactly:
- Do not include any spaces and new lines in the output.
- Output MUST begin with:  Final GSQL: INTERPRET QUERY () FOR GRAPH <graph_name> 
- OUTPUT MUST BE A SINGLE LINE: Do not include line breaks, tabs, or extra spaces.

- If summing, declare this accumulator:  SumAccum<DOUBLE> @totalValue;



"""
    return prompt
