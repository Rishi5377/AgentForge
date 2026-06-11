import re

class ValidatorAgent:
    def validate(self, output: str, role: str) -> str:
        """
        Validates the LLM output for the given role.
        Returns an error string if invalid, or an empty string if valid.
        """
        if not output or not output.strip():
            return "Output was completely empty."
            
        # 1. XML Tag Validation
        if "<agent-" not in output:
            err = (
                "Your output did not contain any `<agent-...>` tags! "
                "You MUST output your code or schema strictly within the requested XML-like tags (e.g., <agent-write path=\"...\"> or <agent-schema>). "
                "Do NOT wrap them in markdown code blocks. Just output the raw tags."
            )
            print(f"VALIDATOR ERROR: {err}\nOUTPUT WAS:\n{output}\n---")
            return err
            
        # 2. Check for unclosed tags
        open_write = output.count("<agent-write")
        close_write = output.count("</agent-write>")
        if open_write != close_write:
            err = f"You have {open_write} <agent-write> tags but {close_write} </agent-write> closing tags. Ensure all tags are properly closed."
            print(f"VALIDATOR ERROR: {err}\nOUTPUT WAS:\n{output}\n---")
            return err
            
        open_schema = output.count("<agent-schema>")
        close_schema = output.count("</agent-schema>")
        if open_schema != close_schema:
            err = f"You have {open_schema} <agent-schema> tags but {close_schema} </agent-schema> closing tags. Ensure all tags are properly closed."
            print(f"VALIDATOR ERROR: {err}\nOUTPUT WAS:\n{output}\n---")
            return err
            
        return "" # No error
