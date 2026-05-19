# Default SimpleAgent workflow

This is the default workflow for diagram prompts.

prompt_start: "diagram"
add_persona_context
add_recent_messages
add_memory_context
add_attachment_context
add_web_context
add_original_user_prompt
add_user_prompt: "Output a mermaid diagram using mermaid code and select the most suitable diagram type if it is not specified."
prompt: "output"
prompt_end