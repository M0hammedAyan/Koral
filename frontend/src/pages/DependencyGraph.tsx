import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { api } from '../services/api';
import { Graph, GraphNode, GraphEdge } from '../types';
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
  correlation?: number;
}

export const DependencyGraph: React.FC = () => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [graph, setGraph] = useState<Graph | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  useEffect(() => {
    api.getGraph().then(setGraph);
  }, []);

  useEffect(() => {
    if (!graph || !svgRef.current) return;

    const width = 800;
    const height = 600;

    d3.select(svgRef.current).selectAll('*').remove();

    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height);

    const nodes: D3Node[] = graph.nodes.map(n => ({ ...n }));
    const links: D3Link[] = graph.edges.map(e => ({ ...e }));

    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id((d: any) => d.id).distance(150))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(40));

    const link = svg.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', '#555')
      .attr('stroke-width', 2);

    const node = svg.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .call(d3.drag<any, D3Node>()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on('drag', (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        })
      );

    node.append('circle')
      .attr('r', 30)
      .attr('fill', (d: D3Node) => d.status === 'problem' ? '#ff6b6b' : '#51cf66')
      .attr('stroke', '#fff')
      .attr('stroke-width', 3)
      .on('click', (event, d) => setSelectedNode(d))
      .on('mouseenter', function() {
        d3.select(this).attr('r', 35);
      })
      .on('mouseleave', function() {
        d3.select(this).attr('r', 30);
      });

    node.append('text')
      .text((d: D3Node) => d.label)
      .attr('text-anchor', 'middle')
      .attr('dy', 5)
      .attr('fill', '#fff')
      .attr('font-size', '12px')
      .attr('pointer-events', 'none');

    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      node.attr('transform', (d: D3Node) => `translate(${d.x},${d.y})`);
    });

  }, [graph]);

  return (
    <div className="dependency-graph">
      <div className="graph-header">
        <h1>Dependency Graph</h1>
        <div className="legend">
          <div className="legend-item">
            <span className="legend-dot normal"></span>
            Normal
          </div>
          <div className="legend-item">
            <span className="legend-dot problem"></span>
            Problem
          </div>
        </div>
      </div>

      <div className="graph-container">
        <svg ref={svgRef}></svg>
      </div>

      {selectedNode && (
        <div className="node-details">
          <h3>Node Details</h3>
          <p><strong>Pod:</strong> {selectedNode.label}</p>
          <p><strong>Status:</strong> {selectedNode.status}</p>
          <button onClick={() => setSelectedNode(null)}>Close</button>
        </div>
      )}
    </div>
  );
};
