"""Assemble the self-contained viewer: three.js and the quantised mesh
buffers are inlined so the page works from a phone with no server."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def build(mesh_json_path, out_path, artifact=False):
    with open(os.path.join(HERE, "viewer_template.html")) as f:
        html = f.read()
    with open(os.path.join(HERE, "vendor_three.min.js")) as f:
        three = f.read()
    with open(mesh_json_path) as f:
        mesh = f.read()
    # The JSON lives inside a <script> element, so a literal "</script>" in
    # it would end the element early; escape the slash to be safe.
    mesh = mesh.replace("</", "<\\/")
    html = html.replace("/*__THREE__*/", three).replace("/*__MESH_JSON__*/", mesh)
    if artifact:
        # The artifact host wraps the page in its own document skeleton, so
        # only the head contents and body contents are kept.
        head = html[html.index("<head>") + 6:html.index("</head>")]
        body = html[html.index("<body>") + 6:html.index("</body>")]
        head = head.replace('<meta charset="utf-8">', "").replace('<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">', "")
        html = head + body
    with open(out_path, "w") as f:
        f.write(html)
    print(f"wrote {out_path} ({os.path.getsize(out_path) / 1e6:.1f} MB)")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    sys.argv = [sys.argv[0]] + args + [a for a in sys.argv[1:] if a.startswith("--")]
    src = sys.argv[1] if len(args) > 0 else os.path.join(HERE, "output", "athena_mesh.json")
    dst = sys.argv[2] if len(args) > 1 else os.path.join(HERE, "output", "athena_viewer.html")
    build(src, dst, artifact="--artifact" in sys.argv)
