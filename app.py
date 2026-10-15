import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import time

# =============================================================================
# 1) PAGE SETUP & CUSTOM GLOBAL CSS
# =============================================================================
st.set_page_config(page_title="Route Lab", page_icon="🗺️", layout="wide")

st.markdown("""
<style>
    /* 1. ปรับขนาดฟอนต์หลักและระยะขอบ */
    .block-container { padding-top: 1rem; padding-bottom: 0rem; max-width: 100%; }
    html, body, [class*="css"] { font-size: 18px !important; }

    /* 2. ปรับขยายขนาดแท็บเมนู (Tabs) */
    button[data-baseweb="tab"] {
        font-size: 20px !important;
        font-weight: 600 !important;
        padding: 10px 20px !important;
    }

    /* 3. ปรับขยาย Sidebar (แถบด้านข้าง) */
    [data-testid="stSidebar"] {
        font-size: 18px !important;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        font-size: 22px !important;
        font-weight: 700 !important;
    }
    [data-testid="stSidebar"] label {
        font-size: 18px !important;
        font-weight: 600 !important;
    }

    /* 4. ปรับขยายช่องกรอกข้อความ (Text Input), Selectbox และ Radio Button */
    div[data-baseweb="input"] input {
        font-size: 18px !important;
        padding: 8px 12px !important;
    }
    div[data-baseweb="select"] div {
        font-size: 18px !important;
    }
    div[class*="stRadio"] label {
        font-size: 18px !important;
    }

    /* 5. ปรับขยายปุ่มกด (Buttons) ใน Sidebar */
    [data-testid="stSidebar"] button {
        font-size: 18px !important;
        padding: 10px 16px !important;
        border-radius: 8px !important;
    }

    /* 6. ตัวเลข Metric */
    div[data-testid="stMetricValue"] { font-size: 28px !important; font-weight: bold; }

    iframe { width: 100% !important; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 2) DATA STRUCTURES INITIALIZATION (เก็บสถานะไว้ใน session_state)
# =============================================================================
DEFAULT_NODES = [
    {'id': 0, 'name': 'จตุจักร', 'en': 'Chatuchak', 'x': 520, 'y': 60},
    {'id': 1, 'name': 'อารีย์', 'en': 'Ari', 'x': 320, 'y': 100},
    {'id': 2, 'name': 'อนุสาวรีย์', 'en': 'Victory Mon.', 'x': 200, 'y': 220},
    {'id': 3, 'name': 'ราชเทวี', 'en': 'Ratchathewi', 'x': 360, 'y': 270},
    {'id': 4, 'name': 'สยาม', 'en': 'Siam', 'x': 480, 'y': 330},
    {'id': 5, 'name': 'ประตูน้ำ', 'en': 'Pratunam', 'x': 600, 'y': 230},
    {'id': 6, 'name': 'อโศก', 'en': 'Asok', 'x': 720, 'y': 350},
    {'id': 7, 'name': 'พร้อมพงษ์', 'en': 'Phrom Phong', 'x': 840, 'y': 440},
    {'id': 8, 'name': 'สีลม', 'en': 'Silom', 'x': 420, 'y': 460},
    {'id': 9, 'name': 'สะพานตากสิน', 'en': 'Saphan Taksin', 'x': 260, 'y': 500},
    {'id': 10, 'name': 'ลาดพร้าว', 'en': 'Ladprao', 'x': 740, 'y': 110},
    {'id': 11, 'name': 'รัชดา', 'en': 'Ratchada', 'x': 840, 'y': 220}
]

DEFAULT_EDGES = [
    {'a': 0, 'b': 1, 'w': 8}, {'a': 0, 'b': 10, 'w': 10}, {'a': 0, 'b': 5, 'w': 16},
    {'a': 1, 'b': 2, 'w': 7}, {'a': 1, 'b': 3, 'w': 12}, {'a': 2, 'b': 3, 'w': 9},
    {'a': 3, 'b': 4, 'w': 6}, {'a': 3, 'b': 5, 'w': 9}, {'a': 4, 'b': 5, 'w': 8},
    {'a': 4, 'b': 6, 'w': 11}, {'a': 5, 'b': 6, 'w': 10}, {'a': 4, 'b': 8, 'w': 12},
    {'a': 8, 'b': 9, 'w': 9}, {'a': 6, 'b': 7, 'w': 7}, {'a': 10, 'b': 11, 'w': 9},
    {'a': 11, 'b': 6, 'w': 12}, {'a': 2, 'b': 9, 'w': 20}, {'a': 8, 'b': 7, 'w': 22}
]

if 'nodes' not in st.session_state:
    st.session_state.nodes = json.loads(json.dumps(DEFAULT_NODES))
if 'edges' not in st.session_state:
    st.session_state.edges = json.loads(json.dumps(DEFAULT_EDGES))

# ดึงข้อมูลจุดที่ยังคงเหลืออยู่จากการแก้ไขล่าสุดบน Canvas
updated_nodes_json = st.query_params.get("deleted_nodes")
if updated_nodes_json:
    try:
        active_ids = set(json.loads(updated_nodes_json))
        st.session_state.nodes = [n for n in st.session_state.nodes if n['id'] in active_ids]
        st.session_state.edges = [e for e in st.session_state.edges if e['a'] in active_ids and e['b'] in active_ids]
    except Exception:
        pass

# ดึงพิกัดย้ายจุดล่าสุดเฉพาะจุดที่มีอยู่แล้ว
updated_positions = st.query_params.get("node_pos")
if updated_positions:
    try:
        pos_data = json.loads(updated_positions)
        for n in st.session_state.nodes:
            str_id = str(n['id'])
            if str_id in pos_data:
                n['x'] = pos_data[str_id]['x']
                n['y'] = pos_data[str_id]['y']
    except Exception:
        pass

updated_edges = st.query_params.get("graph_edges")
if updated_edges:
    try:
        edges_data = json.loads(updated_edges)
        valid_node_ids = set(n['id'] for n in st.session_state.nodes)
        st.session_state.edges = [e for e in edges_data if e['a'] in valid_node_ids and e['b'] in valid_node_ids]
    except Exception:
        pass

# =============================================================================
# 3) SIDEBAR CONTROLS
# =============================================================================
with st.sidebar:
    st.header("⚙️ ตั้งค่า & เพิ่มจุด")
    
    st.subheader("➕ เพิ่มจุดใหม่ตรงนี้")
    new_node_input = st.text_input("ชื่อจุดใหม่ (เช่น บางนา):", key="input_new_node")
    if st.button("➕ กดเพิ่มจุดลงแผนที่"):
        if new_node_input.strip():
            new_id = max([n['id'] for n in st.session_state.nodes] + [-1]) + 1
            node_name = new_node_input.strip()
            
            new_node = {
                'id': new_id,
                'name': node_name,
                'en': node_name,
                'x': 180 + (len(st.session_state.nodes) % 4) * 90,
                'y': 150 + (len(st.session_state.nodes) % 3) * 90
            }
            
            st.session_state.nodes.append(new_node)
            st.query_params.clear()
            st.success(f"เพิ่ม '{node_name}' เรียบร้อยแล้ว!")
            st.rerun()

    st.markdown("---")
    st.subheader("🧮 อัลกอริทึมหลัก")
    algo_choice = st.radio(
        "เลือกอัลกอริทึม",
        options=["Dijkstra", "Prim", "Kruskal"],
        index=0
    )

    st.markdown("---")
    st.subheader("📍 เลือกจุดเชื่อมต่อ")
    
    node_dict = {n['id']: n['name'] for n in st.session_state.nodes}
    node_ids = list(node_dict.keys())
    
    if node_ids:
        start_id = st.selectbox(
            "📍 จุดเริ่มต้น (Start)",
            options=node_ids,
            format_func=lambda x: node_dict.get(x, f"จุด {x}"),
            key="select_start_node"
        )
        
        if algo_choice == "Dijkstra":
            end_id = st.selectbox(
                "🎯 จุดปลายทาง (End)",
                options=node_ids,
                format_func=lambda x: node_dict.get(x, f"จุด {x}"),
                key="select_end_node"
            )
        else:
            end_id = start_id
    else:
        start_id, end_id = 0, 0
        st.warning("ยังไม่มีจุดในระบบ")

    st.markdown("---")
    col_b1, col_b2 = st.columns(2)
    if col_b1.button("🔄 รีเซ็ตแผนที่"):
        st.session_state.nodes = json.loads(json.dumps(DEFAULT_NODES))
        st.session_state.edges = json.loads(json.dumps(DEFAULT_EDGES))
        st.query_params.clear()
        st.rerun()
    if col_b2.button("🗑️ ล้างทั้งหมด"):
        st.session_state.nodes = []
        st.session_state.edges = []
        st.query_params.clear()
        st.rerun()

# =============================================================================
# 4) PYTHON ALGORITHM CALCULATORS
# =============================================================================
def make_key(a, b): return f"{min(a,b)}-{max(a,b)}"

def solve_dijkstra(nodes, edges, s_id, t_id):
    adj = {n['id']: [] for n in nodes}
    for e in edges:
        if e['a'] in adj and e['b'] in adj:
            adj[e['a']].append({'to': e['b'], 'w': e['w']})
            adj[e['b']].append({'to': e['a'], 'w': e['w']})
    
    dist = {n['id']: float('inf') for n in nodes}
    prev = {}
    done = set()
    if s_id in dist: dist[s_id] = 0
    
    while len(done) < len(nodes):
        u = None
        best = float('inf')
        for n in nodes:
            nid = n['id']
            if nid not in done and dist[nid] < best:
                best = dist[nid]
                u = nid
        if u is None or u == t_id: break
        done.add(u)
        
        for item in adj.get(u, []):
            v, w = item['to'], item['w']
            if v not in done and dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                prev[v] = u
                    
    path = []
    curr = t_id
    while curr in prev or curr == s_id:
        path.append(curr)
        if curr == s_id: break
        curr = prev.get(curr)
    path.reverse()
    
    path_edges = [make_key(path[i], path[i+1]) for i in range(len(path) - 1)]
    return dist.get(t_id, float('inf')), path, path_edges

def solve_mst(nodes, edges, s_id):
    if not nodes: return 0, [], False
    node_ids = set([n['id'] for n in nodes])
    start_node = s_id if s_id in node_ids else list(node_ids)[0]
    
    in_t = set([start_node])
    tree_edges = []
    total_w = 0
    
    while len(in_t) < len(nodes):
        best = None
        for e in edges:
            if (e['a'] in in_t) != (e['b'] in in_t):
                if not best or e['w'] < best['w']: best = e
        if not best: break
        nv = best['b'] if best['a'] in in_t else best['a']
        in_t.add(nv)
        tree_edges.append(make_key(best['a'], best['b']))
        total_w += best['w']
        
    is_complete = (len(tree_edges) == len(nodes) - 1)
    return total_w, tree_edges, is_complete

def solve_kruskal(nodes, edges):
    if not nodes: return 0, [], False
    parent = {n['id']: n['id'] for n in nodes}
    def find(i):
        if parent[i] == i:
            return i
        parent[i] = find(parent[i])
        return parent[i]
    
    def union(i, j):
        root_i = find(i)
        root_j = find(j)
        if root_i != root_j:
            parent[root_i] = root_j
            return True
        return False

    sorted_edges = sorted(edges, key=lambda x: x['w'])
    total_w = 0
    mst_edges = []
    
    for e in sorted_edges:
        if e['a'] in parent and e['b'] in parent:
            if union(e['a'], e['b']):
                total_w += e['w']
                mst_edges.append(make_key(e['a'], e['b']))
                
    is_complete = (len(mst_edges) == len(nodes) - 1)
    return total_w, mst_edges, is_complete

# =============================================================================
# 5) MAIN DISPLAY & TABS
# =============================================================================
st.title("🗺️ Route Lab")
st.caption("ทดลองหาเส้นทางและโครงข่ายที่เหมาะสมที่สุดด้วยทฤษฎีกราฟ: Dijkstra, Prim, Kruskal")

tab1, tab2, tab3, tab4 = st.tabs(["📍 ผลลัพธ์", "🎬 แอนิเมชันทีละขั้น", "⚖️ เปรียบเทียบ & วัดเวลา", "✅ ทดสอบความถูกต้อง"])

# --- TAB 1: RESULT ---
with tab1:
    st.subheader(f"📌 ผลลัพธ์การคำนวณอัลกอริทึม {algo_choice}")
    highlight_edges = []
    start_name = node_dict.get(start_id, "เริ่มต้น")
    end_name = node_dict.get(end_id, "ปลายทาง")

    if algo_choice == "Dijkstra":
        cost, path_ids, highlight_edges = solve_dijkstra(st.session_state.nodes, st.session_state.edges, start_id, end_id)
        
        if cost != float('inf') and len(path_ids) > 1:
            path_names = " → ".join([node_dict.get(i, f"จุด {i}") for i in path_ids])
            st.success(f"พบเส้นทางที่เร็วที่สุดจาก **{start_name}** ไปยัง **{end_name}**")
            res_col1, res_col2 = st.columns(2)
            res_col1.metric("เวลารวมสั้นที่สุด", f"{cost} นาที")
            res_col2.metric("จำนวนช่วงเส้นทางที่ผ่าน", f"{len(path_ids)-1} ช่วง")
            st.markdown(f"**ลำดับเส้นทาง:** `{path_names}`")
        else:
            st.error(f"⚠️ **ไม่พบเส้นทางเชื่อมต่อ!** ไม่สามารถเดินทางจาก **'{start_name}'** ไปยัง **'{end_name}'** ได้")
            st.info("💡 **คำแนะนำเพิ่มเติม:** จุดเป้าหมายแยกอยู่อย่างโดดเดี่ยว สามารถสลับไปที่แท็บ **'🎬 แอนิเมชันทีละขั้น'** แล้วใช้เครื่องมือ **`🔗 เชื่อมเส้น`** เพื่อลากเส้นเชื่อมเส้นทางเพิ่มเติมได้ครับ")
            
    elif algo_choice == "Prim":
        mst_cost, highlight_edges, is_complete = solve_mst(st.session_state.nodes, st.session_state.edges, start_id)
        if is_complete:
            st.success("🎉 โครงข่ายต้นไม้ครอบคลุมน้อยที่สุด (MST) สมบูรณ์ด้วย Prim")
            st.metric("เวลารวมของทั้งโครงข่าย (MST)", f"{mst_cost} นาที")
        else:
            st.warning(f"⚠️ **กราฟเชื่อมต่อไม่สมบูรณ์!** ไม่สามารถสร้าง MST ที่ครอบคลุมทุกจุดได้ (ได้เพียง {len(highlight_edges)} จาก {len(st.session_state.nodes)-1} เส้น)")
            st.metric("เวลารวมเส้นเชื่อมที่มี (Forest)", f"{mst_cost} นาที")
            st.info("💡 **คำแนะนำ:** กรุณาใช้เครื่องมือ `🔗 เชื่อมเส้น` ในแท็บแอนิเมชันเพื่อลากเส้นเชื่อมต่อจุดดังกล่าว")
            
    else:
        mst_cost, highlight_edges, is_complete = solve_kruskal(st.session_state.nodes, st.session_state.edges)
        if is_complete:
            st.success("🎉 โครงข่ายต้นไม้ครอบคลุมน้อยที่สุด (MST) สมบูรณ์ด้วย Kruskal")
            st.metric("เวลารวมของทั้งโครงข่าย (MST)", f"{mst_cost} นาที")
        else:
            st.warning(f"⚠️ **กราฟเชื่อมต่อไม่สมบูรณ์!** ไม่สามารถสร้าง MST ที่ครอบคลุมทุกจุดได้ (ได้เพียง {len(highlight_edges)} จาก {len(st.session_state.nodes)-1} เส้น)")
            st.metric("เวลารวมเส้นเชื่อมที่มี (Forest)", f"{mst_cost} นาที")
            st.info("💡 **คำแนะนำ:** กรุณาใช้เครื่องมือ `🔗 เชื่อมเส้น` ในแท็บแอนิเมชันเพื่อลากเส้นเชื่อมต่อจุดดังกล่าว")

    HTML_RESULT_CANVAS = f"""<!doctype html>
    <html lang="th">
    <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=3.0, user-scalable=yes">
    <style>
    :root {{ --rule:#CBD6DC; --edge:#CBD6DC; --route:#0B9A62; --ink:#142A33; --muted:#566F7B; }}
    body {{ margin:0; background:#fff; font-family:"IBM Plex Sans Thai", sans-serif; overflow-x: auto; }}
    .canvas {{ position: relative; width: 100%; height: 620px; overflow: auto; border: 1.5px solid var(--rule); border-radius: 12px; background: #fafafa; touch-action: manipulation; }}
    .canvas svg {{ width: 100%; min-width: 800px; height: 100%; min-height: 550px; display: block; }}
    .edge {{ stroke: var(--edge); stroke-width: 3; stroke-linecap: round; fill: none; }}
    .edge.highlight {{ stroke: var(--route); stroke-width: 8; }}
    .wbox {{ fill: #fff; stroke: var(--rule); stroke-width: 1; }}
    .wtxt {{ fill: var(--muted); font-size: 11px; text-anchor: middle; dominant-baseline: central; font-weight: 500; }}
    .node {{ fill: #fff; stroke: var(--ink); stroke-width: 3; }}
    .node.active {{ fill: #0B9A62; stroke: #142A33; }}
    .nlabel {{ fill: var(--ink); font-size: 13px; font-weight: 600; text-anchor: middle; paint-order: stroke; stroke: #fff; stroke-width: 3px; }}
    .ring {{ fill: none; stroke: var(--route); stroke-width: 3; }}
    </style>
    </head>
    <body>
    <div class="canvas">
      <svg id="svg" viewBox="0 0 1000 560" preserveAspectRatio="xMidYMid meet">
        <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><circle cx="20" cy="20" r="1.3" fill="#cbd6dc"/></pattern>
        <rect width="1000" height="560" fill="url(#grid)"/>
        <g id="layer"></g>
      </svg>
    </div>
    <script>
    (() => {{
      const nodes = {json.dumps(st.session_state.nodes)};
      const edges = {json.dumps(st.session_state.edges)};
      const highlights = {json.dumps(highlight_edges)};
      const startId = {start_id};
      const endId = {end_id};
      const isDijkstra = "{algo_choice}" === "Dijkstra";

      const key = (a, b) => a < b ? a + '-' + b : b + '-' + a;
      const layer = document.getElementById('layer');
      let h = '';

      edges.forEach(e => {{
        let k = key(e.a, e.b);
        let u = nodes.find(n=>n.id===e.a), v = nodes.find(n=>n.id===e.b);
        if(!u || !v) return;
        let isHl = highlights.includes(k);
        h += `<line class="edge ${{isHl ? 'highlight' : ''}}" x1="${{u.x}}" y1="${{u.y}}" x2="${{u.x===v.x?v.x+0.1:v.x}}" y2="${{v.y}}"/>`;
      }});

      edges.forEach(e => {{
        let u = nodes.find(n=>n.id===e.a), v = nodes.find(n=>n.id===e.b);
        if(!u || !v) return;
        let mx = (u.x+v.x)/2, my = (u.y+v.y)/2;
        h += `<g pointer-events="none"><rect class="wbox" x="${{mx-11}}" y="${{my-10}}" width="22" height="20" rx="4"/><text class="wtxt" x="${{mx}}" y="${{my}}">${{e.w}}</text></g>`;
      }});

      nodes.forEach(n => {{
        let isStartOrEnd = isDijkstra ? (n.id === startId || n.id === endId) : (n.id === startId);
        if (isStartOrEnd) {{
          h += `<circle class="ring" cx="${{n.x}}" cy="${{n.y}}" r="18"/>`;
        }}
        h += `<g><circle class="node ${{isStartOrEnd ? 'active' : ''}}" cx="${{n.x}}" cy="${{n.y}}" r="14"/><text class="nlabel" x="${{n.x}}" y="${{n.y+30}}">${{n.name}}</text></g>`;
      }});

      layer.innerHTML = h;
    }})();
    </script>
    </body>
    </html>
    """
    components.html(HTML_RESULT_CANVAS, height=640, scrolling=True)

# --- TAB 2: ANIMATION INTERFACE ---
with tab2:
    HTML_ROUTE_LAB_FULL = f"""<!doctype html>
    <html lang="th">
    <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=3.0, user-scalable=yes">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@400;500;600;700&family=Source+Sans+3:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
    :root {{
      --bg:#FFFFFF; --surface:#FFFFFF; --surface2:#F0F2F6; --ink:#31333F; --muted:#6B7080;
      --rule:#D5D8E0; --primary:#FF4B4B; --primary-hover:#FF6C6C; --on-primary:#FFFFFF;
      --edge:#A3B4BD; --route:#0B9A62; --explore:#2D6BDB; --visit:#F2B01E; --warn:#CF4527;
      --info-bg:rgba(28,131,225,.1); --info-fg:#004280;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; padding:0; background:#fff; font-family:"Source Sans 3","Noto Sans Thai",sans-serif; color:var(--ink); font-size:16px; overflow-x: auto; }}
    
    .wrap {{ width:100%; max-width:1400px; margin:0 auto; padding:10px; }}
    .grid {{ display: grid; grid-template-columns: 1fr 340px; gap: 16px; }}
    @media (max-width: 900px) {{ .grid {{ grid-template-columns: 1fr; }} }}
    
    .card {{ background:var(--surface); border:1px solid var(--rule); border-radius:8px; padding:12px; margin-bottom:12px; }}

    .toolbar {{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; background:var(--surface); border:1px solid var(--rule); border-radius:8px; padding:8px; margin-bottom:12px; }}

    button {{
      background:var(--surface); color:var(--ink); border:1px solid var(--rule); border-radius:6px;
      padding:8px 16px; min-height:42px; cursor:pointer; font-weight:600; font-family:inherit; font-size: 15px;
    }}
    button:hover {{ border-color:var(--primary); color:var(--primary); }}
    button.primary, button[aria-pressed="true"] {{ background:var(--primary); border-color:var(--primary); color:#fff; }}

    .canvas-container {{ position:relative; width:100%; height: 600px; overflow:auto; border:1px solid var(--rule); border-radius:10px; background:#fafafa; touch-action: manipulation; }}
    .canvas-container svg {{ width:100%; min-width: 850px; height:100%; min-height: 550px; display:block; }}
    
    .edge {{ stroke:var(--edge); stroke-width:3; stroke-linecap:round; fill:none; transition: stroke 0.2s, stroke-width 0.2s; }}
    .edge.tree {{ stroke:var(--explore); stroke-width:5; }}
    .edge.path {{ stroke:var(--route); stroke-width:8; }}
    .edge.focus {{ stroke:var(--visit); stroke-width:7; }}
    .hit {{ stroke:transparent; stroke-width:22; fill:none; cursor:pointer; }}
    
    .wbox {{ fill:var(--surface); stroke:var(--rule); stroke-width:1.2; }}
    .wtxt {{ fill:var(--muted); font-size:12px; font-weight:600; text-anchor:middle; dominant-baseline:central; }}
    
    .node {{ fill:var(--surface); stroke:var(--ink); stroke-width:3.5; cursor:grab; transition: fill 0.2s; }}
    .node:active {{ cursor:grabbing; }}
    .node.visited {{ fill:var(--visit); }}
    .node.current {{ fill:var(--explore); }}
    .node.onpath {{ fill:var(--route); }}
    .node.pending {{ stroke:var(--explore); stroke-width:6; }}
    
    .nlabel {{ fill:var(--ink); font-size:14px; font-weight:600; text-anchor:middle; paint-order:stroke; stroke:var(--surface); stroke-width:3.5px; pointer-events:none; }}
    .ring {{ fill:none; stroke:var(--route); stroke-width:3; pointer-events:none; }}
    
    .pop {{ position:absolute; transform:translate(-50%,-130%); background:#fff; border:1px solid var(--primary); border-radius:8px; padding:8px; display:flex; gap:8px; z-index:100; box-shadow:0 4px 12px rgba(0,0,0,0.15); }}
    .pop input {{ width:70px; padding:4px; border:1px solid var(--rule); border-radius:4px; }}

    .ctrl {{ display:grid; grid-template-columns: repeat(3, 1fr); gap:6px; margin-top:8px; }}
    .ctrl .primary {{ grid-column: 1 / -1; }}
    
    .log-box {{ max-height:200px; overflow-y:auto; font-size:13px; background:var(--surface2); padding:8px 12px; border-radius:6px; border:1px solid var(--rule); }}
    .log-box ol {{ margin:0; padding-left:18px; color:var(--muted); }}
    .log-box li.now {{ color:var(--ink); font-weight:600; }}
    .alert {{ padding:10px; border-radius:6px; background:var(--info-bg); color:var(--info-fg); font-weight:500; margin-bottom:8px; font-size: 15px; }}
    .alert.error {{ background:rgba(207,69,39,.1); color:#CF4527; }}
    </style>
    </head>
    <body>

    <div class="wrap">
      <div class="toolbar">
        <div style="display:flex; flex-wrap:wrap; gap:6px;" id="tools">
          <button data-tool="move" aria-pressed="true">🖐️ ลากจุด</button>
          <button data-tool="link" aria-pressed="false">🔗 เชื่อมเส้น</button>
          <button data-tool="weight" aria-pressed="false">⏱️ แก้เวลา</button>
          <button data-tool="del" aria-pressed="false">🗑️ ลบเส้น/จุด</button>
          <button id="btnUndo" style="background:#f0f2f6;">↩️ ย้อนกลับ (Undo)</button>
        </div>
      </div>

      <div class="grid">
        <main>
          <div class="canvas-container" id="canvas">
            <svg id="svg" viewBox="0 0 1000 560" preserveAspectRatio="xMidYMid meet">
              <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><circle cx="20" cy="20" r="1.3" fill="#cbd6dc"/></pattern>
              <rect width="1000" height="560" fill="url(#grid)"/>
              <g id="layer"></g>
            </svg>
            <div class="pop" id="pop" style="display:none;">
              <label style="font-size:14px;">เวลา (นาที) <input id="popIn" type="number" min="1" max="999"></label>
              <button class="primary" id="popOk">ตกลง</button>
            </div>
          </div>
          <p id="hint" style="color:var(--muted); font-size:14px; margin:6px 0 0 0;">ลากจุดเพื่อย้ายตำแหน่ง</p>
        </main>

        <aside>
          <div class="card">
            <h3 style="margin:0 0 8px 0;">🎮 ตัวควบคุมแอนิเมชัน</h3>
            <div class="ctrl">
              <button class="primary" id="btnPlay">▶ เล่นแอนิเมชัน</button>
              <button id="btnNext">ถัดไป ⏭</button>
              <button id="btnBack">⏮ ย้อนกลับ</button>
              <button id="btnReset">🔄 รีเซ็ต</button>
            </div>
            <div style="margin-top:10px;">
              <label style="font-size:13px; color:var(--muted);">ความเร็ว (วินาที):</label>
              <input type="range" id="speed" min="0.1" max="2" step="0.1" value="0.7" style="width:100%;">
            </div>
          </div>

          <div class="alert" id="msg">พร้อมเริ่มสาธิตแอนิเมชัน</div>

          <div class="card">
            <h4 style="margin:0 0 6px 0;">📋 บันทึกขั้นตอนการทำงาน</h4>
            <div class="log-box"><ol id="log"></ol></div>
          </div>
        </aside>
      </div>
    </div>

    <script>
    (() => {{
      const W = 1000, H = 560;
      let nodes = JSON.parse(JSON.stringify({json.dumps(st.session_state.nodes)}));
      let edges = JSON.parse(JSON.stringify({json.dumps(st.session_state.edges)}));
      const algo = "{algo_choice.lower()}";
      let startId = {start_id};
      let endId = {end_id};
      let tool = "move";

      let historyStack = [];

      function saveHistory() {{
        historyStack.push({{
          nodes: JSON.parse(JSON.stringify(nodes)),
          edges: JSON.parse(JSON.stringify(edges))
        }});
        if (historyStack.length > 20) historyStack.shift();
      }}

      const key = (a, b) => a < b ? a + '-' + b : b + '-' + a;
      const $ = id => document.getElementById(id);
      const svg = $('svg'), layer = $('layer');

      let pending = null, drag = null, weightEdge = null;
      let steps = [], idx = -1, timer = null;

      const N = id => nodes.find(n => n.id === id && !n.isDeleted);
      const nm = id => N(id) ? N(id).name : '?';
      const pathTo = (prev, t) => {{ const p = [t]; while (prev[p[0]] !== undefined) p.unshift(prev[p[0]]); return p; }};
      const edgesOfPath = p => p.slice(1).map((v, i) => key(p[i], v));

      function hidePop() {{
        $('pop').style.display = 'none';
        weightEdge = null;
      }}

      function syncStateToStreamlit() {{
        const posMap = {{}};
        nodes.filter(n => !n.isDeleted).forEach(n => {{ posMap[n.id] = {{ x: Math.round(n.x), y: Math.round(n.y) }}; }});
        const activeNodeIds = nodes.filter(n => !n.isDeleted).map(n => n.id);
        try {{
          const u = new URL(window.parent.location.href);
          u.searchParams.set('node_pos', JSON.stringify(posMap));
          u.searchParams.set('graph_edges', JSON.stringify(edges));
          u.searchParams.set('deleted_nodes', JSON.stringify(activeNodeIds));
          window.parent.history.replaceState({{}}, '', u.toString());
        }} catch(e) {{}}
      }}

      const HINTS = {{
        move: 'ลากจุดเพื่อย้ายตำแหน่ง',
        link: 'คลิกจุดแรก แล้วคลิกจุดที่สองเพื่อเชื่อมเส้น',
        weight: 'คลิกที่เส้นเพื่อแก้ไขเวลาเดินทาง (นาที)',
        del: 'คลิกจุดหรือเส้นที่ต้องการลบ'
      }};

      document.querySelectorAll('#tools button[data-tool]').forEach(b => b.addEventListener('click', () => {{
        tool = b.dataset.tool; pending = null; hidePop();
        document.querySelectorAll('#tools button[data-tool]').forEach(btn => btn.setAttribute('aria-pressed', String(btn === b)));
        $('hint').textContent = HINTS[tool];
        render();
      }}));

      $('btnUndo').onclick = () => {{
        if (historyStack.length > 0) {{
          const lastState = historyStack.pop();
          nodes = lastState.nodes;
          edges = lastState.edges;
          syncStateToStreamlit();
          updateGraphState();
        }}
      }};

      function buildSteps() {{
        steps = [];
        const activeNodes = nodes.filter(n => !n.isDeleted);
        
        if (algo === 'dijkstra') {{
          const adj = {{}}; activeNodes.forEach(n => adj[n.id] = []);
          edges.forEach(e => {{ 
            if(adj[e.a] && adj[e.b]) {{
              adj[e.a].push(Object.assign({{}}, {{ to: e.b, w: e.w }})); 
              adj[e.b].push(Object.assign({{}}, {{ to: e.a, w: e.w }})); 
            }}
          }});
          
          const dist = {{}}, prev = {{}}, done = new Set();
          activeNodes.forEach(n => dist[n.id] = Infinity); 
          if(N(startId)) dist[startId] = 0;

          steps.push(Object.assign({{}}, {{ msg: 'เริ่มที่ ' + nm(startId) + ' ตั้งระยะเป็น 0 นาที', current: startId, visited: [] }}));

          for (;;) {{
            let u = null, best = Infinity;
            for (const n of activeNodes) if (!done.has(n.id) && dist[n.id] < best) {{ best = dist[n.id]; u = n.id; }}
            if (u === null) break;
            done.add(u);

            steps.push(Object.assign({{}}, {{
              msg: 'พิจารณาจุด ' + nm(u) + ' (ระยะสั้นสุดในกลุ่ม = ' + best + ' นาที) -> ยืนยันระยะ',
              current: u, visited: [...done], treeEdges: Object.keys(prev).map(v => key(+v, prev[v]))
            }}));

            if (u === endId) break;

            for (const item of (adj[u] || [])) {{
              const to = item.to, w = item.w;
              if (done.has(to)) continue;
              const nd = dist[u] + w;
              if (nd < dist[to]) {{
                dist[to] = nd; prev[to] = u;
                steps.push(Object.assign({{}}, {{
                  msg: 'สแกนผ่าน ' + nm(u) + ' ไป ' + nm(to) + ' (ได้ ' + nd + ' นาที) -> อัปเดตทางเลือกใหม่',
                  current: u, focus: key(u, to), visited: [...done], treeEdges: Object.keys(prev).map(v => key(+v, prev[v]))
                }}));
              }}
            }}
          }}

          if (dist[endId] !== Infinity && dist[endId] !== undefined) {{
            const p = pathTo(prev, endId);
            steps.push(Object.assign({{}}, {{
              msg: '🎉 ได้เส้นทางสั้นที่สุดจาก ' + nm(startId) + ' ไป ' + nm(endId) + ' รวม ' + dist[endId] + ' นาที!',
              pathNodes: p, pathEdges: edgesOfPath(p), visited: [...done]
            }}));
          }} else {{
            steps.push(Object.assign({{}}, {{
              msg: '⚠️ ไม่สามารถเดินทางไปถึง ' + nm(endId) + ' ได้ (ไม่มีเส้นทางเชื่อมต่อ)',
              visited: [...done], isError: true
            }}));
          }}
        }} else if (algo === 'prim') {{
          let inT = new Set([startId]), tree = [];
          steps.push(Object.assign({{}}, {{ msg: 'เริ่ม Prim จากจุด ' + nm(startId), current: startId, visited: [startId] }}));
          
          while (inT.size < activeNodes.length) {{
            let best = null;
            edges.forEach(e => {{
              if (inT.has(e.a) !== inT.has(e.b) && (!best || e.w < best.w)) best = e;
            }});
            if (!best) break;
            let nv = inT.has(best.a) ? best.b : best.a;
            inT.add(nv); tree.push(key(best.a, best.b));
            steps.push(Object.assign({{}}, {{
              msg: 'เลือกเส้น ' + nm(best.a) + '-' + nm(best.b) + ' (น้ำหนัก ' + best.w + ') ไปจุด ' + nm(nv),
              current: nv, visited: [...inT], focus: key(best.a, best.b), pathEdges: [...tree]
            }}));
          }}

          if (tree.length === activeNodes.length - 1) {{
            steps.push(Object.assign({{}}, {{
              msg: '🎉 สำเร็จ! สร้าง Minimum Spanning Tree (MST) ครอบคลุมครบทุกจุดแล้ว',
              pathEdges: [...tree], visited: [...inT]
            }}));
          }} else {{
            steps.push(Object.assign({{}}, {{
              msg: '⚠️ กราฟไม่เชื่อมต่อกัน! เชื่อมได้เพียง ' + inT.size + '/' + activeNodes.length + ' จุด (หลุดเป็น Forest)',
              pathEdges: [...tree], visited: [...inT], isError: true
            }}));
          }}

        }} else if (algo === 'kruskal') {{
          const parent = {{}};
          activeNodes.forEach(n => parent[n.id] = n.id);
          function find(i) {{
            if (parent[i] === i) return i;
            return parent[i] = find(parent[i]);
          }}
          function union(i, j) {{
            const rootI = find(i), rootJ = find(j);
            if (rootI !== rootJ) {{ parent[rootI] = rootJ; return true; }}
            return false;
          }}

          const validEdges = edges.filter(e => N(e.a) && N(e.b));
          const sortedEdges = [...validEdges].sort((x, y) => x.w - y.w);
          const tree = [];
          const visitedNodes = new Set();

          steps.push(Object.assign({{}}, {{ msg: 'เริ่ม Kruskal: เรียงลำดับเส้นเชื่อมทั้งหมดตามน้ำหนักจากน้อยไปมาก', visited: [] }}));

          for (const e of sortedEdges) {{
            const k = key(e.a, e.b);
            if (union(e.a, e.b)) {{
              tree.push(k);
              visitedNodes.add(e.a);
              visitedNodes.add(e.b);
              steps.push(Object.assign({{}}, {{
                msg: 'เลือกเส้นสั้นที่สุดถัดไป ' + nm(e.a) + '-' + nm(e.b) + ' (น้ำหนัก ' + e.w + ') -> ไม่เกิดวงรอบ (Circle)',
                focus: k,
                pathEdges: [...tree],
                visited: [...visitedNodes]
              }}));
            }} else {{
              steps.push(Object.assign({{}}, {{
                msg: 'ข้ามเส้น ' + nm(e.a) + '-' + nm(e.b) + ' (น้ำหนัก ' + e.w + ') -> เกิดวงรอบ (Circle)',
                focus: k,
                pathEdges: [...tree],
                visited: [...visitedNodes]
              }}));
            }}
            if (tree.length === activeNodes.length - 1) break;
          }}

          if (tree.length === activeNodes.length - 1) {{
            steps.push(Object.assign({{}}, {{
              msg: '🎉 สำเร็จ! ได้ Minimum Spanning Tree (MST) ครอบคลุมครบ ' + activeNodes.length + ' จุด',
              pathEdges: [...tree], visited: [...visitedNodes]
            }}));
          }} else {{
            steps.push(Object.assign({{}}, {{
              msg: '⚠️ ไม่สามารถสร้าง MST สมบูรณ์ได้! ได้เพียง ' + tree.length + ' เส้น จากที่ต้องการ ' + (activeNodes.length - 1) + ' เส้น (หลุดเป็น Forest)',
              pathEdges: [...tree], visited: [...visitedNodes], isError: true
            }}));
          }}
        }}
      }}

      function render() {{
        const st = idx >= 0 ? steps[idx] : null;
        const tree = new Set(st && st.treeEdges || []);
        const path = new Set(st && st.pathEdges || []);
        const visited = new Set(st && st.visited || []);
        const onPath = new Set(st && st.pathNodes || []);

        let h = '';

        edges.forEach(e => {{
          const k = key(e.a, e.b), a = N(e.a), b = N(e.b);
          if (!a || !b) return;
          let cls = "edge";
          if (st && st.focus === k) cls += " focus";
          else if (path.has(k)) cls += " path";
          else if (tree.has(k)) cls += " tree";
          h += `<line class="${{cls}}" x1="${{a.x}}" y1="${{a.y}}" x2="${{a.x===b.x?b.x+0.1:b.x}}" y2="${{b.y}}"/>`;
        }});

        edges.forEach((e, i) => {{
          const a = N(e.a), b = N(e.b);
          if (!a || !b) return;
          h += `<line class="hit" data-edge="${{i}}" x1="${{a.x}}" y1="${{a.y}}" x2="${{b.x}}" y2="${{b.y}}"/>`;
        }});

        edges.forEach(e => {{
          const a = N(e.a), b = N(e.b);
          if (!a || !b) return;
          const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
          h += `<g pointer-events="none"><rect class="wbox" x="${{mx-11}}" y="${{my-10}}" width="22" height="20" rx="4"/><text class="wtxt" x="${{mx}}" y="${{my}}">${{e.w}}</text></g>`;
        }});

        const activeNodes = nodes.filter(n => !n.isDeleted);
        activeNodes.forEach(n => {{
          let cls = "node";
          if (visited.has(n.id)) cls += " visited";
          if (st && st.current === n.id) cls += " current";
          if (onPath.has(n.id)) cls += " onpath";
          if (pending === n.id) cls += " pending";

          h += `<g data-node="${{n.id}}">`;
          let isTargetNode = (algo === 'dijkstra') ? (n.id === startId || n.id === endId) : (n.id === startId);
          if (isTargetNode) {{
            h += `<circle class="ring" cx="${{n.x}}" cy="${{n.y}}" r="18"/>`;
          }}
          h += `<circle class="${{cls}}" cx="${{n.x}}" cy="${{n.y}}" r="13"/><text class="nlabel" x="${{n.x}}" y="${{n.y+28}}">${{n.name}}</text></g>`;
        }});

        layer.innerHTML = h;

        if (st && st.isError) {{
          $('msg').className = 'alert error';$('msg').textContent = 'ขั้นที่ ' + (idx + 1) + '/' + steps.length + ': ' + st.msg;
        }} else {{
          $('msg').className = 'alert';$('msg').textContent = st ? ('ขั้นที่ ' + (idx + 1) + '/' + steps.length + ': ' + st.msg) : 'พร้อมเริ่มสาธิตแอนิเมชัน กด "เล่นแอนิเมชัน"';
        }}
        
        let logHTML = '';
        for (let i = 0; i <= idx; i++) {{
          logHTML += `<li class="${{i === idx ? 'now' : ''}}">${{steps[i].msg}}</li>`;
        }}
        $('log').innerHTML = logHTML;
        $('log').scrollTop =$('log').scrollHeight;
      }}

      function pt(e) {{
        const p = svg.createSVGPoint(); p.x = e.clientX; p.y = e.clientY;
        const r = p.matrixTransform(svg.getScreenCTM().inverse());
        return {{ x: Math.max(30, Math.min(W - 30, Math.round(r.x))), y: Math.max(30, Math.min(H - 30, Math.round(r.y))) }};
      }}

      svg.addEventListener('pointerdown', e => {{
        const nEl = e.target.closest('[data-node]'), eEl = e.target.closest('[data-edge]');
        
        if (tool !== 'weight') hidePop();
        
        if (tool === 'move') {{
          if (nEl) {{ saveHistory(); drag = nodes.find(n => n.id === +nEl.dataset.node); svg.setPointerCapture(e.pointerId); }}
        }} else if (tool === 'link') {{
          if (nEl) {{
            const id = +nEl.dataset.node;
            if (pending === null) {{ pending = id; render(); }}
            else if (pending !== id) {{
              if (!edges.some(eg => key(eg.a, eg.b) === key(pending, id))) {{
                saveHistory();
                edges.push({{ a: pending, b: id, w: 10 }});
                syncStateToStreamlit();
              }}
              pending = null; updateGraphState();
            }} else {{ pending = null; render(); }}
          }} else {{ pending = null; render(); }}
        }} else if (tool === 'weight') {{
          if (eEl) {{
            weightEdge = +eEl.dataset.edge;
            const eg = edges[weightEdge], u = N(eg.a), v = N(eg.b);
            $('pop').style.left = ((u.x + v.x) / 2 / W * 100) + '%';
            $('pop').style.top = ((u.y + v.y) / 2 / H * 100) + '\%';$('pop').style.display = 'flex'; 
            $('popIn').value = eg.w; $('popIn').focus();
          }} else {{ hidePop(); }}
        }} else if (tool === 'del') {{
          if (nEl) {{
            saveHistory();
            const id = +nEl.dataset.node;
            nodes = nodes.map(n => n.id === id ? Object.assign({{}}, n, {{ isDeleted: true }}) : n);
            edges = edges.filter(eg => eg.a !== id && eg.b !== id);
            syncStateToStreamlit();
            updateGraphState();
          }} else if (eEl) {{
            saveHistory();
            edges.splice(+eEl.dataset.edge, 1);
            syncStateToStreamlit();
            updateGraphState();
          }}
        }}
      }});

      svg.addEventListener('pointermove', e => {{
        if (!drag) return;
        const p = pt(e); drag.x = p.x; drag.y = p.y; render();
      }});

      const stopDrag = () => {{
        if (drag) {{
          drag = null;
          syncStateToStreamlit();
        }}
      }};
      svg.addEventListener('pointerup', stopDrag);
      svg.addEventListener('pointercancel', stopDrag);

      $('popOk').onclick = () => {{
        if (weightEdge !== null && edges[weightEdge]) {{
          saveHistory();
          edges[weightEdge].w = +$('popIn').value || 1;
          hidePop(); 
          syncStateToStreamlit();
          updateGraphState();
        }}
      }};

      $('popIn').onkeydown = e => {{
        if (e.key === 'Enter') $('popOk').click();
        if (e.key === 'Escape') hidePop();
      }};

      function updateGraphState() {{ stop(); steps = []; idx = -1; buildSteps(); render(); }}

      function next() {{ if (idx < steps.length - 1) {{ idx++; render(); return true; }} stop(); return false; }}
      function back() {{ stop(); if (idx > 0) {{ idx--; render(); }} }}
      function reset() {{ stop(); idx = -1; render(); }}
      function stop() {{ if (timer) {{ clearInterval(timer); timer = null; }} $('btnPlay').textContent = '▶ เล่นแอนิเมชัน'; }}
      function play() {{
        if (timer) {{ stop(); return; }}
        if (idx >= steps.length - 1) idx = -1;
        $('btnPlay').textContent = '⏸ หยุด';
        timer = setInterval(() => {{ if (!next()) stop(); }}, +$('speed').value * 1000);
        next();
      }}

      $('btnPlay').onclick = play;
      $('btnNext').onclick = () => {{ stop(); next(); }};$('btnBack').onclick = back;
      $('btnReset').onclick = reset;

      buildSteps(); 
      render();
    }})();
    </script>
    </body>
    </html>
    """
    components.html(HTML_ROUTE_LAB_FULL, height=750, scrolling=True)

# --- TAB 3: REAL-TIME BENCHMARKING ---
with tab3:
    st.subheader("⚖️ เปรียบเทียบประสิทธิภาพและการวัดเวลาจริง (Real-Time Benchmarking)")
    
    nodes = st.session_state.nodes
    edges = st.session_state.edges
    
    if not nodes:
        st.warning("⚠️ ไม่พบข้อมูลกราฟ กรุณาเพิ่มจุดและเส้นเชื่อมก่อนทำการวัดผล")
    else:
        t0 = time.perf_counter()
        dijk_cost, dijk_path, _ = solve_dijkstra(nodes, edges, start_id, end_id)
        t1 = time.perf_counter()
        dijk_time_ms = (t1 - t0) * 1000

        t0 = time.perf_counter()
        prim_cost, _, _ = solve_mst(nodes, edges, start_id)
        t1 = time.perf_counter()
        prim_time_ms = (t1 - t0) * 1000

        t0 = time.perf_counter()
        kruskal_cost, _, _ = solve_kruskal(nodes, edges)
        t1 = time.perf_counter()
        kruskal_time_ms = (t1 - t0) * 1000

        st.markdown("#### 📊 ตารางเปรียบเทียบผลลัพธ์จากกราฟปัจจุบัน:")
        
        bench_data = [
            {
                "อัลกอริทึม": "Dijkstra",
                "วัตถุประสงค์": "หาเส้นทางสั้นสุด (Shortest Path)",
                "ผลลัพธ์รวม (นาที)": f"{dijk_cost:.1f} นาที" if dijk_cost != float('inf') else "ไม่มีเส้นทาง",
                "เวลาประมวลผลจริง": f"{dijk_time_ms:.4f} ms"
            },
            {
                "อัลกอริทึม": "Prim",
                "วัตถุประสงค์": "ต้นไม้ครอบคลุมน้อยที่สุด (MST)",
                "ผลลัพธ์รวม (นาที)": f"{prim_cost:.1f} นาที",
                "เวลาประมวลผลจริง": f"{prim_time_ms:.4f} ms"
            },
            {
                "อัลกอริทึม": "Kruskal",
                "วัตถุประสงค์": "ต้นไม้ครอบคลุมน้อยที่สุด (MST)",
                "ผลลัพธ์รวม (นาที)": f"{kruskal_cost:.1f} นาที",
                "เวลาประมวลผลจริง": f"{kruskal_time_ms:.4f} ms"
            }
        ]

        df_bench = pd.DataFrame(bench_data)
        st.dataframe(df_bench, use_container_width=True, hide_index=True)

        fastest_mst = "Prim" if prim_time_ms <= kruskal_time_ms else "Kruskal"
        st.info(f"⚡ **สรุปประสิทธิภาพ:** บนกราฟปัจจุบัน ({len(nodes)} จุด, {len(edges)} เส้นเชื่อม) อัลกอริทึมสร้าง MST ที่ประมวลผลได้เร็วที่สุดคือ **{fastest_mst}**")

# --- TAB 4: REAL DYNAMIC VALIDATION (คงการตรวจ Prim & Kruskal และแสดงกล่องเตือนเป๊ะตามภาพ) ---
with tab4:
    st.subheader("✅ ผลการทดสอบความถูกต้องของกราฟ")
    
    nodes = st.session_state.nodes
    edges = st.session_state.edges
    
    if not nodes:
        st.warning("⚠️ แผนที่ยังไม่มีจุดใดๆ ในระบบ")
    else:
        # 1. คำนวณหา Adjacency List และ Connected Components
        adj = {n['id']: set() for n in nodes}
        for e in edges:
            if e['a'] in adj and e['b'] in adj:
                adj[e['a']].add(e['b'])
                adj[e['b']].add(e['a'])
                
        # หาจุดโดดเดี่ยว (ไม่มีเส้นเชื่อมเลย)
        isolated_nodes = [n for n in nodes if len(adj[n['id']]) == 0]
        
        # นับจำนวนกลุ่มกราฟย่อย (Components)
        visited_comp = set()
        components_list = []
        for n in nodes:
            nid = n['id']
            if nid not in visited_comp:
                comp = []
                q = [nid]
                visited_comp.add(nid)
                while q:
                    curr = q.pop(0)
                    comp.append(curr)
                    for neighbor in adj[curr]:
                        if neighbor not in visited_comp:
                            visited_comp.add(neighbor)
                            q.append(neighbor)
                components_list.append(comp)
        
        is_fully_connected = (len(components_list) == 1)
        
        # 2. ทดสอบความถูกต้องเฉพาะของอัลกอริทึม Prim และ Kruskal
        _, _, prim_complete = solve_mst(nodes, edges, start_id)
        _, _, kruskal_complete = solve_kruskal(nodes, edges)

        # 3. แสดงรายงานสถานะกราฟปัจจุบัน
        st.markdown("#### 🔍 รายงานสถานะกราฟปัจจุบัน:")
        
        col_v1, col_v2, col_v3 = st.columns(3)
        col_v1.metric("จำนวนจุดทั้งหมด (Nodes)", f"{len(nodes)} จุด")
        col_v2.metric("จำนวนเส้นเชื่อม (Edges)", f"{len(edges)} เส้น")
        col_v3.metric("สถานะความเชื่อมโยง", "เชื่อมครบถ้วน" if is_fully_connected else "มีจุดแยกโดดเดี่ยว")
        
        st.markdown("---")
        
        # 4. กล่องแสดงเตือนตรงตามรูปแบบในภาพ
        if is_fully_connected and prim_complete and kruskal_complete:
            st.success("✅ **สมบูรณ์:** ทุกจุดเชื่อมต่อกันเป็นเครือข่ายเดียว (Connected Graph) สามารถใช้อัลกอริทึม Dijkstra, Prim และ Kruskal ได้ 100%")
        else:
            # คำนวณหาจำนวนจุดที่ไม่สามารถเดินทางไปถึงได้จากกลุ่มหลัก
            main_comp_size = max([len(c) for c in components_list]) if components_list else 0
            unreachable_count = len(nodes) - main_comp_size
            
            # แสดงกล่องแจ้งเตือนสีแดง
            st.error(f"❌ **กราฟไม่เชื่อมต่อกันสมบูรณ์ (Disconnected Graph):** สำรวจพบ {unreachable_count} จุดที่ไม่สามารถเดินทางไปถึงได้จากจุดอื่น")
            
        # แสดงกล่องเตือนสีเหลืองเมื่อมีจุดโดดเดี่ยว
        if isolated_nodes:
            iso_names = ", ".join([n['name'] for n in isolated_nodes])
            st.warning(f"⚠️ **พบจุดโดดเดี่ยว (ไม่มีเส้นเชื่อมเลย):** {iso_names}")
            st.info("💡 **แนะนำ:** ใช้เครื่องมือ `🔗 เชื่อมเส้น` ในแท็บแอนิเมชันเพื่อลากเส้นเชื่อมต่อจุดดังกล่าว")

        # 5. สรุปความพร้อมการทำงานของ Prim และ Kruskal
        st.markdown("#### 🧮 การรองรับของ Prim & Kruskal:")
        col_p, col_k = st.columns(2)
        if prim_complete:
            col_p.success("✅ **Prim Algorithm:** พร้อมสร้าง Minimum Spanning Tree (MST) ครอบคลุมครบทุกจุด")
        else:
            col_p.warning("⚠️ **Prim Algorithm:** สร้างได้เพียงโครงข่ายย่อย (Spanning Forest) เนื่องจากกราฟไม่เชื่อมต่อกัน")
            
        if kruskal_complete:
            col_k.success("✅ **Kruskal Algorithm:** พร้อมสร้าง Minimum Spanning Tree (MST) ครอบคลุมครบทุกจุด")
        else:
            col_k.warning("⚠️ **Kruskal Algorithm:** สร้างได้เพียงโครงข่ายย่อย (Spanning Forest) เนื่องจากกราฟไม่เชื่อมต่อกัน")
