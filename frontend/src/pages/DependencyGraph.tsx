import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as d3 from 'd3';
import { api, wsService } from '../services/api';
import { Graph, GraphNode } from '../types';
import '../styles/DependencyGraph.css';

interface D3Node extends GraphNode {
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

interface D3Link {
  source: D3Node | string;
  target: D3Node | string;
}

export const DependencyGraph: React.FC = () => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [graph, setGraph] = useState<Graph>({ nodes: [], edges: [] });
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>('');

  const loadGraph = useCallback(async () => {
    const data = await api.getGraph();
    setGraph(data);
    if (data.nodes.length > 0) {
      setLastUpdated(new Date().toLocaleTimeString());
    }
  }, []);

  // Poll every 5s + refresh on every incident WebSocket event
  useEffect(() => {
    loadGraph();
    wsService.subscribe((msg: any) => {
      if (msg?.type === 'incident') loadGraph();
    });
    const interval = setInterval(loadGraph, 5000);
    return () => clearInterval(interval);
  }, [loadGraph]);

  // Redraw D3 whenever graph data changes
  useEffect(() => {
    if (!svgRef.current) return;

    const width = 800;
    const height = 500;

    d3.select(svgRef.current).selectAll('*').remove();

    if (graph.nodes.length === 0) return;

    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height);

    const nodes: D3Node[] = graph.nodes.map(n => ({ ...n }));
    const links: D3Link[] = graph.edges.map(e => ({ ...e }));

    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id((d: any) => d.id).distance(180))
      .force('charge', d3.forceManyBody().strength(-400))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(50));

    const link = svg.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', '#444')
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', '5,3');

    const node = svg.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .call(d3.drag<any, D3Node>()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x; d.fy = d.y;
        })
        .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y; })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null; d.fy = null;
        })
      );

    // Outer glow ring for problem nodes
    node.append('circle')
      .attr('r', 36)
      .attr('fill', 'none')
      .attr('stroke', (d: D3Node) => d.status === 'problem' ? '#ff6b6b' : '#51cf66')
      .attr('stroke-width', 2)
      .attr('opacity', 0.3);

    node.append('circle')
      .attr('r', 28)
      .attr('fill', (d: D3Node) => d.status === 'problem' ? '#ff6b6b33' : '#51cf6633')
      .attr('stroke', (d: D3Node) => d.status === 'problem' ? '#ff6b6b' : '#51cf66')
      .attr('stroke-width', 2.5)
      .on('click', (_event, d) => setSelectedNode(d))
      .on('mouseenter', function () { d3.select(this).attr('r', 33); })
      .on('mouseleave', function () { d3.select(this).attr('r', 28); });

    node.append('text')
      .text((d: D3Node) => d.label)
      .attr('text-anchor', 'middle')
      .attr('dy', 4)
      .attr('fill', '#fff')
      .attr('font-size', '11px')
      .attr('font-weight', '600')
      .attr('pointer-events', 'none');

    // Status label below node
    node.append('text')
      .text((d: D3Node) => d.status === 'problem' ? '⚠ problem' : '✓ normal')
      .attr('text-anchor', 'middle')
      .attr('dy', 44)
      .attr('fill', (d: D3Node) => d.status === 'problem' ? '#ff6b6b' : '#51cf66')
      .attr('font-size', '10px')
      .attr('pointer-events', 'none');

    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);
      node.attr('transform', (d: D3Node) => `translate(${d.x ?? 0},${d.y ?? 0})`);
    });

  }, [graph]);

  return (
    <div className="dependency-graph">
      <div className="graph-header">
        <h1>Dependency Graph</h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          {lastUpdated && (
            <span style={{ fontSize: '0.8rem', color: '#666' }}>
              Last updated: {lastUpdated}
            </span>
          )}
          <div className="legend">
            <div className="legend-item">
              <span className="legend-dot normal"></span> Normal
            </div>
            <div className="legend-item">
              <span className="legend-dot problem"></span> Problem
            </div>
          </div>
        </div>
      </div>

      <div className="graph-container">
        {graph.nodes.length === 0 ? (
          <div style={{
            height: '400px', display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center', color: '#555', gap: '0.5rem'
          }}>
            <div style={{ fontSize: '2rem' }}>🔗</div>
            <div>No pod relationships yet</div>
            <div style={{ fontSize: '0.85rem', color: '#444' }}>
              Graph populates automatically when anomalies are detected
            </div>
          </div>
        ) : (
          <svg ref={svgRef}></svg>
        )}
      </div>

      {selectedNode && (
        <div className="node-details">
          <h3>Pod Details</h3>
          <p><strong>Pod:</strong> {selectedNode.label}</p>
          <p><strong>Status:</strong>
            <span style={{ color: selectedNode.status === 'problem' ? '#ff6b6b' : '#51cf66', marginLeft: '0.5rem' }}>
              {selectedNode.status === 'problem' ? '⚠ Problem detected' : '✓ Normal'}
            </span>
          </p>
          <button onClick={() => setSelectedNode(null)}>Close</button>
        </div>
      )}
    </div>
  );
};
