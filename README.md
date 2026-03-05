# OpRoomManager

A Python-based optimization project for managing operating room (surgical room) scheduling and resource allocation.

## Overview

This repository contains three different algorithmic approaches to solving the operating room scheduling problem—a complex optimization challenge in healthcare logistics. Each implementation represents a distinct strategy for optimizing operating room utilization and procedure scheduling.

## Files

### 1. **VRP3indices.py**
A Vehicle Routing Problem (VRP) variant implementation with 3-index formulation. This approach models the operating room scheduling as a routing optimization problem, using a mathematical programming approach to optimize room assignments and scheduling.

### 2. **fin_quirofanos.py** 
A comprehensive implementation focused on operating room ("quirófanos" in Spanish) optimization with advanced constraints and objective functions. This solution likely incorporates practical healthcare constraints and performance metrics.

### 3. **prueba-final-conjunto-inicial-naive.py**
A naive/heuristic-based approach that uses initial solution construction methods. This simpler algorithm provides a baseline solution strategy, useful for comparison and quick approximations.

## Purpose

These three files demonstrate different optimization paradigms:
- **Mathematical Programming** (VRP3indices) - Exact or near-exact solutions using formal optimization models
- **Advanced Constraints** (fin_quirofanos) - Domain-specific optimization with practical healthcare rules
- **Heuristic Methods** (Naive approach) - Fast, approximate solutions for large-scale problems

## Technologies

- Python 3.x
- Mathematical/optimization libraries (likely numpy, scipy, or optimization solvers)

## Use Cases

- Hospital operating room scheduling
- Surgical procedure allocation
- Resource optimization for healthcare facilities
- Comparison of optimization methodologies

---

*Choose the implementation that best fits your performance requirements, scalability needs, and available computational resources.*
