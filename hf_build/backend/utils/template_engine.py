import os
import shutil
import json
import subprocess
import random

class TemplateEngine:
    def __init__(self, templates_dir: str):
        self.templates_dir = templates_dir
        self.manifests_dir = os.path.join(templates_dir, 'manifests')
        self.source_files_dir = os.path.join(templates_dir, 'source_files')
        self.clean_starters_dir = os.path.join(templates_dir, 'clean_starters')
        self.blocks_dir = os.path.join(templates_dir, 'blocks')
        self.backend_blocks_dir = os.path.join(templates_dir, 'backend_blocks')

    def copy_blocks(self, blocks: list, dest_dir: str):
        if not blocks: return
        components_dir = os.path.join(dest_dir, 'src', 'components', 'blocks')
        os.makedirs(components_dir, exist_ok=True)
        for block in blocks:
            src_block = os.path.join(self.blocks_dir, block)
            if os.path.exists(src_block):
                shutil.copy2(src_block, os.path.join(components_dir, block))
                print(f"Injected frontend block: {block}")
            else:
                print(f"Warning: Block {block} not found in {self.blocks_dir}")

    def copy_backend_blocks(self, blocks: list, dest_dir: str):
        if not blocks: return
        backend_dir = os.path.join(dest_dir, 'src', 'backend_blocks')
        os.makedirs(backend_dir, exist_ok=True)
        for block in blocks:
            src_block = os.path.join(self.backend_blocks_dir, block)
            if os.path.exists(src_block):
                shutil.copy2(src_block, os.path.join(backend_dir, block))
                print(f"Injected backend block: {block}")
            else:
                print(f"Warning: Backend block {block} not found in {self.backend_blocks_dir}")

    def get_manifest(self, template_id: str):
        manifest_path = os.path.join(self.manifests_dir, f"{template_id}.json")
        if not os.path.exists(manifest_path):
            raise ValueError(f"Template '{template_id}' manifest not found.")
        with open(manifest_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def instantiate_template(self, template_id: str, dest_dir: str, project_name: str = "MyProject", author: str = "AgentForge"):
        # 1. Read manifest
        manifest = self.get_manifest(template_id)

        source_dir = os.path.join(self.source_files_dir, template_id)
        if not os.path.exists(source_dir):
            raise ValueError(f"Source files for '{template_id}' not found.")

        # 2. Copy source files (excluding any unwanted hidden folders if necessary, though it should be clean)
        if os.path.exists(dest_dir):
            shutil.rmtree(dest_dir)
        shutil.copytree(source_dir, dest_dir, ignore=shutil.ignore_patterns('node_modules', '.next', 'dist'))

        # 3. Inject clean starters
        for file_name in os.listdir(self.clean_starters_dir):
            src_file = os.path.join(self.clean_starters_dir, file_name)
            dest_file = os.path.join(dest_dir, file_name)
            
            with open(src_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace variables
            content = content.replace("{{PROJECT_NAME}}", project_name)
            content = content.replace("{{AUTHOR}}", author)

            with open(dest_file, 'w', encoding='utf-8') as f:
                f.write(content)

        # 3.5 Inject Random Famous Company Design System
        try:
            design_systems_dir = os.path.expanduser("~/.gemini/antigravity/knowledge/open-design/design-systems")
            if os.path.exists(design_systems_dir):
                # Get list of valid design system folders (must contain DESIGN.md and tokens.css)
                available_systems = []
                for ds in os.listdir(design_systems_dir):
                    ds_path = os.path.join(design_systems_dir, ds)
                    if os.path.isdir(ds_path) and not ds.startswith("_"):
                        if os.path.exists(os.path.join(ds_path, "DESIGN.md")) and os.path.exists(os.path.join(ds_path, "tokens.css")):
                            available_systems.append(ds_path)
                
                if available_systems:
                    chosen_ds_path = random.choice(available_systems)
                    ds_name = os.path.basename(chosen_ds_path)
                    print(f"Injecting Design System: {ds_name}")
                    
                    # Read tokens.css
                    with open(os.path.join(chosen_ds_path, "tokens.css"), "r", encoding="utf-8") as f:
                        tokens_content = f.read()
                    
                    # Inject tokens into index.css
                    index_css_path = os.path.join(dest_dir, "src", "index.css")
                    if os.path.exists(index_css_path):
                        with open(index_css_path, "r", encoding="utf-8") as f:
                            current_css = f.read()
                        with open(index_css_path, "w", encoding="utf-8") as f:
                            # Prepend tokens below tailwind import
                            f.write(current_css + "\n\n/* Injected Design System Tokens */\n" + tokens_content)
                    
                    # Copy DESIGN.md to project root
                    shutil.copy2(os.path.join(chosen_ds_path, "DESIGN.md"), os.path.join(dest_dir, "DESIGN.md"))
        except Exception as e:
            print(f"Failed to inject design system: {e}")

        # 4. Update package.json name if it exists
        pkg_path = os.path.join(dest_dir, 'package.json')
        if os.path.exists(pkg_path):
            with open(pkg_path, 'r', encoding='utf-8') as f:
                pkg = json.load(f)
            pkg['name'] = project_name.lower().replace(" ", "-")
            with open(pkg_path, 'w', encoding='utf-8') as f:
                json.dump(pkg, f, indent=2)

        print(f"Skipping native dependency hydration for {template_id} to save memory. Will hydrate asynchronously later.")

        return {"status": "success", "template": template_id, "manifest": manifest}
