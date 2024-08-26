# Copyright 2020, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
  This module defines logic to create a resource utilization network
  graph for HERON Simulations.
"""
import networkx as nx
import matplotlib as mpl
mpl.use('Agg') # Prevents the module from blocking while plotting
import matplotlib.pyplot as plt
import plotly.graph_objects as go  
from collections import defaultdict


class NetworkPlot:
  """
   Represents a network graph visualization of the resources found
   in a HERON system.
  """

  def __init__(self, components: list) -> None:
    """
      Initialize the network plot.
      @ In, components, list, the components defined by the input file.
      @ Out, None
    """
    self._components = components
    self._resources = set()
    self._producers_and_consumers = set()
    self._capacities = {}
    self._edges = []
    self._graph = nx.DiGraph()
    self._find_nodes_and_edges()
    self._plot_graph()
    self._build_table()

  def _find_nodes_and_edges(self) -> None:
    """
      Iterate over the components to determine nodes and their
      associated directional edges.
      @ In, None
      @ Out, None
    """
    for c in self._components:
      self._producers_and_consumers.add(c.name)

      rsc_in = c.get_inputs()
      for ri in rsc_in:
        self._resources.add(ri)
        self._graph.add_edge(ri, c.name)
        self._edges.append((ri, c.name))

      rsc_out = c.get_outputs()
      for ro in rsc_out:
        self._resources.add(ro)
        self._graph.add_edge(c.name, ro)
        self._edges.append((c.name, ro))

  def _build_table(self) -> None:
    """
      Table should have two major sections: economic info and optimization parameters

      Economic info:
        - Cash flows (just the names?)
        - Lifetime?

      Optimization settings:
        - dispatch (fixed, independent, dependent)
        - optimized, swept, or fixed?
        - capacity (optimization bounds, sweep values, or fixed value)

      @ In, None
      @ Out, None
    """
    col_labels = ['Dispatchable?', 'Governed?']
    cell_text = []
    row_labels = []

    for c in self._components:
      row_labels.append(c.name)
      cell_text.append([c.is_dispatchable(), c.is_governed()])

    plt.table(cell_text, rowLabels=row_labels, colLabels=col_labels, loc='bottom')

  def _plot_graph(self) -> None:
    """
      Plots and formats the graph
      @ In, None
      @ Out, None
    """
    tech_options = {  # TODO make this something that can be done dynamically
      "node_size": 1000,
      "node_color": "#FCEDDA",
      "edgecolors": "#FCEDDA",
      "linewidths": 1
    }

    resrc_options = {
      "node_size": 1500,
      "node_color": "#EE4E34",
      "edgecolors": "#EE4E34",
      "linewidths": 1
    }

    label_options = {
      "font_size": 8,
      "font_weight": "normal",
      "font_color": "black",
    }

    edge_options = {
      'edge_color': 'black',
      "width": 1,
      'arrows': True,
      'arrowsize': 20
    }

    fig, ax = plt.subplots(figsize=(7,7))
    pos = nx.circular_layout(self._graph)

    nx.draw_networkx_nodes(self._graph, pos, nodelist=list(self._resources), **resrc_options)
    nx.draw_networkx_nodes(self._graph, pos, nodelist=list(self._producers_and_consumers), **tech_options)
    nx.draw_networkx_labels(self._graph, pos, **label_options)
    nx.draw_networkx_edges(self._graph, pos, node_size=1500, **edge_options)

    ax.axis('off')
    fig.set_facecolor('darkgrey')

  def generate_plotly(self,casename:str|None, casemode:str|None, html_path:str|None):
     """
       Plots and formats the graph
       @ In, html_path, string, base path for saving the html plot
       @ Out, None
     """
     # Products are the starting point of the plot
     nodes = []
     #Information to display when hovering over the nodes
     customData = []
     hovertemplate = "Dispactchable: %{customdata[1]} <br>"
     hovertemplate+= "Governed: %{customdata[0]} <br>"
     hovertemplate+= "Lifetime: %{customdata[2]} <br>"
     #Intended form: Will be used to break cycles for storage nodes
     #  {"resource_name: : { "consumer" : [index], "producer" : [index]}}
     rsc = defaultdict(lambda: defaultdict(lambda: []))
     #Enumerate components because Plotly like indexes
     for i,c in enumerate(self._components):
       #Identify nodes
       if c.name not in nodes:
           #Generate custom hover information for each node in the network
           nodes.append(c.name)
           customData.append(
                   [c.is_governed(),
                    c.is_dispatchable(),
                    c._economics._lifetime,
                    ])
           print(c.get_capacity)

       #Match nodes
       rsc_in = c.get_inputs()
       for ri in rsc_in:
           rsc[ri]["consumer"].append(i)

       rsc_out = c.get_outputs()
       for ro in rsc_out:
           rsc[ro]["producer"].append(i)

     # create the links
     lnk_lbl = []
     lnk_src = []
     lnk_tgt = []
     lnk_val = []
     for r in rsc.keys():
         for j in rsc[r]["producer"]:
             for k in rsc[r]["consumer"]:
                 if j != k: #Storage nodes produce and consume but are not cycles
                     lnk_lbl.append(r)
                     lnk_src.append(j)
                     lnk_tgt.append(k)
                     lnk_val.append(1)

     fig = go.Figure(go.Sankey(
         arrangement='freeform',
         textfont=dict(
             size = 18,
             ),
         hoverlabel_font_size = 18,
         node=dict(
             label=nodes,
             pad=10,
             align="right",
             customdata = customData,
             hovertemplate = hovertemplate,
         ),
         link=dict(
             arrowlen=15,
             source = lnk_src ,
             target = lnk_tgt ,
             value  = lnk_val ,
             label  = lnk_lbl,
         ),

     ))
     fig.update_layout(title_text=f"Case Name: {casename}  Mode: {casemode}")
     fig.write_html(html_path + "plotly_network.html")

  def save(self, filename: str) -> None:
    """
      Save resource graph to file
      @ In, filename, str, path to file
      @ Out, None
    """
    plt.savefig(filename)
