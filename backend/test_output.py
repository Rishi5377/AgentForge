import asyncio
import re

async def main():
    process = await asyncio.create_subprocess_exec(
        "pnpm.cmd", "run", "dev", "--", "--port", "50000",
        cwd="workspace/app_75dd7689-b972-4abb-b561-5c3d4554fd6e",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    while True:
        line = await process.stdout.readline()
        if not line:
            break
        text = line.decode('utf-8', errors='ignore').strip()
        print(f"RAW: {repr(text)}")
        clean_text = re.sub(r'\x1b\[[0-9;]*m', '', text)
        clean_text = clean_text.replace('\u001b', '')
        print(f"CLEAN: {repr(clean_text)}")
        
        if "Local:" in clean_text and "http://localhost:" in clean_text:
            match = re.search(r'http://localhost:(\d+)', clean_text)
            print(f"MATCH: {match}")
            if match:
                print(f"GROUP: {match.group(1)}")
                break

asyncio.run(main())
