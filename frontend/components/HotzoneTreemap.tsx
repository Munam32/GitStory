"use client";

import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

interface FileData {
  name: string;
  path: string;
  churn_score: number;
  total_commits: number;
  last_modified: string;
}

interface HotzoneTreemapProps {
  data: FileData[];
  onFileClick: (file: FileData) => void;
}

const HotzoneTreemap: React.FC<HotzoneTreemapProps> = ({ data, onFileClick }) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!svgRef.current || !data.length) return;

    // Clear previous SVG content
    d3.select(svgRef.current).selectAll('*').remove();

    const width = 1000;
    const height = 600;

    const svg = d3.select(svgRef.current)
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('width', '100%')
      .attr('height', 'auto')
      .style('font-family', 'Inter, sans-serif');

    // Create hierarchy
    // First, group by directory if possible, but the request says "files sized by churn score"
    // and "clicking a file rectangle opens a side panel".
    // We'll create a flat hierarchy under a root node for simplicity, or 
    // we can build a proper tree structure from paths.
    
    const rootData = {
      name: 'root',
      children: data
    };

    const root = d3.hierarchy<any>(rootData)
      .sum((d: any) => d.churn_score || 0)
      .sort((a, b) => (b.value || 0) - (a.value || 0));

    const treemapLayout = d3.treemap<any>()
      .size([width, height])
      .paddingOuter(3)
      .paddingTop(19)
      .paddingInner(1)
      .round(true);

    treemapLayout(root);

    // Color scale: Green for low churn, Red for high churn
    const maxChurn = d3.max(data, d => d.churn_score) || 1;
    const colorScale = d3.scaleSequential()
      .domain([0, maxChurn])
      .interpolator(d3.interpolateRgb('rgb(34, 197, 94)', 'rgb(239, 68, 68)')); // tailwind green-500 to red-500

    const nodes = svg.selectAll('g')
      .data(root.leaves() as d3.HierarchyRectangularNode<any>[])
      .enter()
      .append('g')
      .attr('transform', d => `translate(${d.x0},${d.y0})`);

    nodes.append('rect')
      .attr('width', d => d.x1 - d.x0)
      .attr('height', d => d.y1 - d.y0)
      .attr('fill', d => colorScale((d.data as FileData).churn_score))
      .attr('stroke', '#fff')
      .style('cursor', 'pointer')
      .on('mouseover', function (event, d) {
        d3.select(this).attr('opacity', 0.8);
        const file = d.data as FileData;
        const tooltip = d3.select(tooltipRef.current);
        tooltip.style('visibility', 'visible')
          .html(`
            <div style="font-weight: bold; margin-bottom: 4px;">${file.path}</div>
            <div>Churn Score: ${file.churn_score}</div>
            <div>Total Commits: ${file.total_commits}</div>
            <div>Last Modified: ${new Date(file.last_modified).toLocaleDateString()}</div>
          `);
      })
      .on('mousemove', function (event) {
        d3.select(tooltipRef.current)
          .style('top', (event.pageY - 10) + 'px')
          .style('left', (event.pageX + 10) + 'px');
      })
      .on('mouseout', function () {
        d3.select(this).attr('opacity', 1);
        d3.select(tooltipRef.current).style('visibility', 'hidden');
      })
      .on('click', (event, d) => {
        onFileClick(d.data as FileData);
      });

    nodes.append('text')
      .attr('x', 5)
      .attr('y', 15)
      .text(d => {
          const w = d.x1 - d.x0;
          const label = (d.data as FileData).name;
          return w > label.length * 7 ? label : '';
      })
      .attr('font-size', '12px')
      .attr('fill', 'white')
      .style('pointer-events', 'none');

  }, [data, onFileClick]);

  return (
    <div style={{ position: 'relative', width: '100%' }}>
      <svg ref={svgRef}></svg>
      <div 
        ref={tooltipRef}
        style={{
          position: 'absolute',
          visibility: 'hidden',
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          color: 'white',
          padding: '8px 12px',
          borderRadius: '4px',
          fontSize: '12px',
          pointerEvents: 'none',
          zIndex: 1000,
          whiteSpace: 'nowrap'
        }}
      ></div>
    </div>
  );
};

export default HotzoneTreemap;
