import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import numpy as np
import json
import os
try:
    import networkx as nx
except ImportError:
    nx = None
try:
    import plotly.graph_objs as go
    from plotly.utils import PlotlyJSONEncoder
except ImportError:
    pass

# Set non-interactive backend
matplotlib.use('Agg')

def apply_theme(fig=None):
    """Applies dark theme to matplotlib figures."""
    plt.style.use('dark_background')
    if fig:
        fig.patch.set_facecolor('#1e1e1e')

def plot_resource_trends(faction_data: pd.DataFrame, output_path: str):
    """Generates a line chart of resource trends."""
    apply_theme()
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(faction_data['turn'], faction_data['requisition'], label='Requisition', color='#4CAF50')
    if 'promethium' in faction_data.columns:
        ax.plot(faction_data['turn'], faction_data['promethium'], label='Promethium', color='#FF9800')
        
    ax.set_title("Resource Trends")
    ax.set_xlabel("Turn")
    ax.set_ylabel("Quantity")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

def plot_military_power_evolution(faction_data: pd.DataFrame, output_path: str):
    """Generates an area chart of military power over time."""
    apply_theme()
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # columns: turn, military_power
    ax.fill_between(faction_data['turn'], faction_data['military_power'], color='#F44336', alpha=0.4)
    ax.plot(faction_data['turn'], faction_data['military_power'], color='#D32F2F', label='Military Power')
        
    ax.set_title("Military Power Evolution")
    ax.set_xlabel("Turn")
    ax.set_ylabel("Power Score")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

def plot_network_graph(nodes: list, edges: list, output_path: str):
    """Draws a network graph (e.g., diplomacy or portals)."""
    if not nx: return
    apply_theme()
    
    G = nx.Graph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)
    
    fig, ax = plt.subplots(figsize=(10, 10))
    pos = nx.spring_layout(G, seed=42)
    
    nx.draw_networkx_nodes(G, pos, node_color='#2196F3', node_size=500, alpha=0.9, ax=ax)
    nx.draw_networkx_edges(G, pos, edge_color='#ffffff', alpha=0.5, ax=ax)
    nx.draw_networkx_labels(G, pos, font_color='white', ax=ax)
    
    ax.set_title("Network Graph")
    ax.axis('off')
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

def plot_battle_intensity_heatmap(battle_data: pd.DataFrame, output_path: str):
    """Generates a heatmap of battle intensity (System vs Turn)."""
    apply_theme()
    
    # Pivot: Index=System, Columns=Turn, Values=Intensity(Rounds/Casualties)
    pivot = battle_data.pivot_table(index='planet', columns='turn', values='rounds', aggfunc='sum', fill_value=0)
    
    fig, ax = plt.subplots(figsize=(12, 8))
    im = ax.imshow(pivot.values, cmap='magma', aspect='auto')
    
    ax.set_title("Battle Intensity Heatmap")
    ax.set_xlabel("Turn")
    ax.set_ylabel("System")
    
    # Add colorbar
    cbar = plt.colorbar(im)
    cbar.set_label('Rounds Fought')
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

def plot_tech_progression(tech_data: pd.DataFrame, output_path: str):
    """Generates a step line chart of cumulative tech unlocks."""
    apply_theme()
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.step(tech_data['turn'], tech_data['cumulative_techs'], where='post', color='#00BCD4', label='Techs Unlocked')
    
    ax.set_title("Tech Progression")
    ax.set_xlabel("Turn")
    ax.set_ylabel("Cumulative Unlocks")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

def plot_diplomacy_network(edges: list, output_path: str):
    """Network graph for diplomacy."""
    factions = list(set([n for e in edges for n in e]))
    plot_network_graph(factions, edges, output_path)

def plot_portal_network(portal_df: pd.DataFrame, output_path: str):
    """Network graph for portals."""
    if portal_df.empty: return
    
    # Edges: source=faction?, target=location? 
    # Actually portal patterns might just be hubs. 
    # Let's map Usage: Faction -> Location as edge
    edges = []
    nodes = set()
    for _, row in portal_df.iterrows():
        edges.append((row['faction'], row['location']))
        nodes.add(row['faction'])
        nodes.add(row['location'])
        
    plot_network_graph(list(nodes), edges, output_path)

def create_interactive_resource_chart(faction_data: pd.DataFrame) -> str:
    """Returns Plotly JSON for interactive dashboard chart."""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=faction_data['turn'], 
        y=faction_data['requisition'],
        mode='lines',
        name='Requisition',
        line=dict(color='#00ff00')
    ))
    
    fig.update_layout(
        title="Interactive Resource Trends",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#ffffff')
    )
    
    return json.dumps(fig, cls=PlotlyJSONEncoder)

def create_tech_tree_sunburst(tech_data: list) -> str:
    """Creates a Sunburst chart for tech progression."""
    # tech_data = [{'id': 'tech_1', 'parent': '', 'label': 'Basic'}, ...]
    
    ids = [t['id'] for t in tech_data]
    labels = [t['label'] for t in tech_data]
    parents = [t['parent'] for t in tech_data]
    
    fig = go.Figure(go.Sunburst(
        ids=ids,
        labels=labels,
        parents=parents,
        branchvalues="total"
    ))
    
    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0))
    return json.dumps(fig, cls=PlotlyJSONEncoder)
