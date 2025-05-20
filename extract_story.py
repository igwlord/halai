import re
import json

def extract_story_content(html_content):
    try:
        # Find the start of the storyContent object
        # We are looking for "var storyContent = {"
        # Making it flexible with spacing and ensuring '{' is captured.
        match = re.search(r"var\s+storyContent\s*=\s*({)", html_content, re.DOTALL)
        if not match:
            # Fallback for cases where storyContent might not be declared with 'var'
            # or has a slightly different assignment. This is less specific.
            match = re.search(r"storyContent\s*=\s*({)", html_content, re.DOTALL)
            if not match:
                return None

        # Get the starting position of the object (the opening brace)
        start_char_index = match.start(1) # This is the index of '{'
        
        open_braces = 0
        # Iterate from the character where '{' was found
        for i in range(start_char_index, len(html_content)):
            char = html_content[i]
            if char == '{':
                open_braces += 1
            elif char == '}':
                open_braces -= 1
                if open_braces == 0:
                    # We found the final closing brace of the object
                    # The object string is from start_char_index to i (inclusive)
                    json_str_candidate = html_content[start_char_index : i+1]
                    
                    potential_semicolon_index = i + 1
                    while potential_semicolon_index < len(html_content) and html_content[potential_semicolon_index].isspace():
                        potential_semicolon_index += 1
                    
                    if potential_semicolon_index < len(html_content) and html_content[potential_semicolon_index] == ';':
                        try:
                            parsed_json = json.loads(json_str_candidate)
                            return json.dumps(parsed_json, indent=4)
                        except json.JSONDecodeError:
                            # This can happen if the object literal is not valid JSON
                            # (e.g. uses single quotes, trailing commas, comments)
                            # Fall through to alternative methods if direct parse fails
                            pass 
        
        # Fallback: If brace counting didn't cleanly find "};"
        # try regex for `var storyContent = { ... };`
        alt_match = re.search(r"var\s+storyContent\s*=\s*({.*?})\s*;", html_content, re.DOTALL)
        if not alt_match:
            # Fallback if not declared with var
            alt_match = re.search(r"storyContent\s*=\s*({.*?})\s*;", html_content, re.DOTALL)

        if alt_match:
            json_str = alt_match.group(1)
            try:
                # Try direct parsing first
                parsed_json = json.loads(json_str)
                return json.dumps(parsed_json, indent=4)
            except json.JSONDecodeError:
                 # Attempt to fix common JS-to-JSON issues if direct parsing fails
                 # 1. Replace single quotes with double quotes for keys and string values
                 json_str_fixed = re.sub(r"(\W)'(\w+)'(\W*):", r'\1"\2"\3:', json_str) # Keys
                 json_str_fixed = re.sub(r":\s*'([^']*)'", r': "\1"', json_str_fixed)   # Values
                 # 2. Remove trailing commas (from arrays or objects)
                 json_str_fixed = re.sub(r",\s*([\}\]])", r"\1", json_str_fixed)
                 try:
                     parsed_json = json.loads(json_str_fixed)
                     return json.dumps(parsed_json, indent=4)
                 except json.JSONDecodeError:
                     return None # Still couldn't parse
        return None

    except Exception as e:
        # To help debug, you might want to print the error to stderr
        # import sys
        # print(f"Error in extract_story_content: {e}", file=sys.stderr)
        return None

if __name__ == "__main__":
    html_file_path = "sample_story.html"
    output_json_file_path = "story_content.json" # As per instruction to return *only* the object

    try:
        with open(html_file_path, "r", encoding="utf-8") as f:
            html = f.read()
    except FileNotFoundError:
        import sys
        sys.stderr.write(f"Error: HTML file '{html_file_path}' not found.\n")
        sys.exit(1)
    
    story_json_output = extract_story_content(html)
    
    if story_json_output:
        try:
            with open(output_json_file_path, "w", encoding="utf-8") as f_out:
                f_out.write(story_json_output)
            # If run directly and successfully, there will be no stdout, only the file.
            # For bash execution, this is fine.
        except IOError:
            import sys
            sys.stderr.write(f"Error: Could not write to output file '{output_json_file_path}'.\n")
            sys.exit(1)
    else:
        import sys
        sys.stderr.write("Error: storyContent object not found or could not be parsed.\n")
        sys.exit(1)
