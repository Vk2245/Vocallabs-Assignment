import markdown
import sys

def convert_md_to_html(md_file, html_file):
    with open(md_file, 'r', encoding='utf-8') as f:
        md_text = f.read()

    html = markdown.markdown(md_text, extensions=['tables', 'fenced_code'])
    
    # Simple CSS for preview, with print-specific fixes
    css = """
    <style>
        body { font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: 0 auto; padding: 20px; }
        h1, h2, h3 { border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }
        table { border-collapse: collapse; width: 100%; margin-bottom: 20px; table-layout: auto; }
        th, td { border: 1px solid #dfe2e5; padding: 8px 12px; vertical-align: top; }
        th { background-color: #f6f8fa; font-weight: 600; }
        
        /* Force long URLs/code to wrap so they don't break the table width */
        code { background-color: rgba(27,31,35,0.05); padding: 0.2em 0.4em; border-radius: 3px; font-family: SFMono-Regular,Consolas,monospace; overflow-wrap: anywhere; word-break: break-word; white-space: pre-wrap; }
        
        @media print {
            body { max-width: 100%; padding: 0; margin: 0; font-size: 13px; }
            table { width: 100%; page-break-inside: auto; }
            tr { page-break-inside: avoid; page-break-after: auto; }
            /* Give standard columns some breathing room so they never squish */
            td:first-child, th:first-child { min-width: 80px; }
        }
    </style>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({ startOnLoad: true });
        // The python markdown library generates <code class="language-mermaid">. 
        // We need to change these to <div class="mermaid"> for Mermaid to process them.
        document.addEventListener("DOMContentLoaded", function() {
            const elements = document.querySelectorAll("code.language-mermaid");
            elements.forEach(el => {
                const div = document.createElement("div");
                div.className = "mermaid";
                div.textContent = el.textContent;
                el.parentNode.replaceWith(div);
            });
            mermaid.run();
        });
    </script>
    """
    
    full_html = f"<html><head><meta charset='utf-8'><title>Vocallabs Final Teardown</title>{css}</head><body>{html}</body></html>"
    
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(full_html)
    
if __name__ == "__main__":
    convert_md_to_html("README.md", "README_Preview.html")
