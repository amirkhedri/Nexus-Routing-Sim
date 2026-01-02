import math
import heapq
import datetime
import copy
from typing import Dict, List, Tuple, Optional

# Constants used in logic
INFINITY = 9999

class LSA:
    """Link State Advertisement Packet"""
    def __init__(self, origin_id, seq, neighbors, area):
        self.origin_id = origin_id
        self.seq_num = seq
        self.neighbors = neighbors
        self.area_id = area
        self.is_summary = False

class LinkStateDB:
    """Database for storing topology maps"""
    def __init__(self):
        self.database = {}
    
    def update(self, lsa):
        existing = self.database.get(lsa.origin_id)
        if not existing or lsa.seq_num > existing.seq_num:
            self.database[lsa.origin_id] = lsa
            return True
        return False
    
    def get_graph(self):
        graph = {}
        for lsa in self.database.values():
            if lsa.origin_id not in graph: graph[lsa.origin_id] = {}
            for nid, cost in lsa.neighbors:
                graph[lsa.origin_id][nid] = cost
                if nid not in graph: graph[nid] = {}
        return graph

class Router:
    """Virtual Router Node"""
    def __init__(self, rid, x, y, area=0):
        self.id = rid
        self.x = x
        self.y = y
        self.area_id = area
        self.is_abr = False
        
        # Tables
        self.routing_table = {} # {dest: (next_hop, cost)}
        self.lsdb = LinkStateDB()
        self.lsa_seq = 0
        self.distance_vector = {}
        self.bgp_paths = {}

    def reset(self):
        self.routing_table = {}
        self.lsdb = LinkStateDB()
        self.lsa_seq = 0
        self.distance_vector = {}
        self.bgp_paths = {}

    def create_lsa(self, neighbors):
        self.lsa_seq += 1
        return LSA(self.id, self.lsa_seq, neighbors, self.area_id)

class Link:
    """Physical Connection"""
    def __init__(self, r1, r2, cost):
        self.r1 = r1
        self.r2 = r2
        self.cost = cost
        self.active = True

class NetworkSimulator:
    """The Brain: Handles protocol execution and topology"""
    def __init__(self):
        self.routers = {}
        self.links = []
        self.protocol = "Link-State (OSPF)"
        self.areas_enabled = False
        self.scenario = "Complex (Default)"
        self.load_scenario(self.scenario)

    def load_scenario(self, name):
        self.scenario = name
        self.routers.clear()
        self.links.clear()
        
        if name == "Simple Ring":
            nodes = ['A', 'B', 'C', 'D', 'E']
            coords = [(300, 100), (500, 150), (550, 350), (300, 400), (100, 250)]
            for i, rid in enumerate(nodes):
                self.routers[rid] = Router(rid, coords[i][0], coords[i][1], 0)
            for i in range(len(nodes)):
                self.links.append(Link(nodes[i], nodes[(i+1)%len(nodes)], 1))
        
        elif name == "Full Mesh":
            nodes = {'A':(200,200), 'B':(500,200), 'C':(200,500), 'D':(500,500)}
            for rid, pos in nodes.items():
                self.routers[rid] = Router(rid, pos[0], pos[1], 0)
            ids = list(nodes.keys())
            for i in range(len(ids)):
                for j in range(i+1, len(ids)):
                    self.links.append(Link(ids[i], ids[j], 5))
        
        else: # "Complex (Default)"
            locs = {
                'A':(150,250,0), 'B':(300,100,0), 'C':(300,400,0),
                'D':(500,250,0), 'E':(700,100,1), 'F':(700,400,1)
            }
            for rid, (x, y, area) in locs.items():
                self.routers[rid] = Router(rid, x, y, area)
            self.routers['D'].is_abr = True
            
            self.links = [
                Link('A','B',2), Link('A','C',5), Link('B','C',2),
                Link('B','D',3), Link('C','D',1), Link('D','E',4),
                Link('D','F',2), Link('E','F',1)
            ]

    def get_neighbors(self, rid):
        n = []
        for l in self.links:
            if not l.active: continue
            if l.r1 == rid: n.append((l.r2, l.cost))
            elif l.r2 == rid: n.append((l.r1, l.cost))
        return n
    
    def get_link(self, r1, r2):
        for l in self.links:
            if (l.r1==r1 and l.r2==r2) or (l.r1==r2 and l.r2==r1): return l
        return None

    def run_simulation(self):
        for r in self.routers.values(): r.reset()
        if self.protocol == "Link-State (OSPF)": return self._run_ospf()
        elif "RIP" in self.protocol: return self._run_rip()
        elif "BGP" in self.protocol: return self._run_bgp()
        return []

    # --- OSPF IMPLEMENTATION ---
    def _run_ospf(self):
        logs = [f"Initialized OSPF. Areas: {self.areas_enabled}"]
        
        # 1. Intra-Area Flooding
        queue = []
        for rid, r in self.routers.items():
            lsa = r.create_lsa(self.get_neighbors(rid))
            r.lsdb.update(lsa) # Self update
            for nid, _ in self.get_neighbors(rid):
                queue.append({'from':rid, 'to':nid, 'lsa':lsa})
        self._flood(queue, logs, "Phase 1")
        
        # 2. Inter-Area Summaries
        if self.areas_enabled:
            logs.append("Generating ABR Summaries...")
            sum_q = []
            abrs = [r for r in self.routers.values() if r.is_abr]
            for abr in abrs:
                g = abr.lsdb.get_graph()
                dists, _ = self._dijkstra(g, abr.id)
                
                # Area 1 -> 0
                s0 = [(d, dists[d]) for d,r in self.routers.items() if r.area_id!=0 and d in dists and dists[d]<INFINITY]
                if s0:
                    l = LSA(f"{abr.id}-SUM-A0", 1, s0+[(abr.id,0)], 0)
                    l.is_summary = True
                    sum_q.append({'from':abr.id, 'lsa':l})
                
                # Area 0 -> 1
                s1 = [(d, dists[d]) for d,r in self.routers.items() if r.area_id!=1 and d in dists and dists[d]<INFINITY]
                if s1:
                    l = LSA(f"{abr.id}-SUM-A1", 1, s1+[(abr.id,0)], 1)
                    l.is_summary = True
                    sum_q.append({'from':abr.id, 'lsa':l})
            
            # Flood Summaries
            fq = []
            for item in sum_q:
                self.routers[item['from']].lsdb.update(item['lsa'])
                for nid, _ in self.get_neighbors(item['from']):
                    fq.append({'from':item['from'], 'to':nid, 'lsa':item['lsa']})
            self._flood(fq, logs, "Phase 2")
            
        # 3. Dijkstra Calculation
        logs.append("Calculating Shortest Paths...")
        for rid, r in self.routers.items():
            g = r.lsdb.get_graph()
            
            # FIX: Inject Link from ABR to Summary Node
            for n in list(g.keys()):
                if "SUM" in n:
                    abr = n.split("-")[0]
                    if abr in g: g[abr][n] = 0
            
            dists, parents = self._dijkstra(g, rid)
            
            for dest in self.routers:
                if dest == rid:
                    r.routing_table[dest] = ("Local", 0)
                    continue
                
                # Try direct path
                nh, cost = None, INFINITY
                if dest in dists:
                    cost = dists[dest]
                    nh = self._get_nh(rid, dest, parents)
                else:
                    # Try via Summary
                    best_sc, best_sn = INFINITY, None
                    for n in g:
                        if "SUM" in n and dest in g[n] and n in dists:
                            tc = dists[n] + g[n][dest]
                            if tc < best_sc: best_sc, best_sn = tc, n
                    if best_sc < INFINITY:
                        cost = best_sc
                        nh = self._get_nh(rid, best_sn, parents)
                
                if nh: r.routing_table[dest] = (nh, int(cost))
                else: r.routing_table[dest] = ("?", "∞")
        
        logs.append("Convergence Complete.")
        return logs

    def _flood(self, queue, logs, phase):
        q = copy.copy(queue)
        seen = set()
        count = 0
        while q:
            pkt = q.pop(0)
            uniq = (pkt['to'], pkt['lsa'].origin_id, pkt['lsa'].seq_num)
            if uniq in seen: continue
            seen.add(uniq)
            
            rcv = self.routers[pkt['to']]
            snd = self.routers[pkt['from']]
            lsa = pkt['lsa']
            
            accept = False
            if not self.areas_enabled: accept = True
            elif lsa.is_summary: accept = (lsa.area_id == rcv.area_id)
            elif lsa.area_id == rcv.area_id or rcv.is_abr or snd.is_abr: accept = True
            
            if accept and rcv.lsdb.update(lsa):
                count += 1
                for nid, _ in self.get_neighbors(rcv.id):
                    if nid != snd.id: q.append({'from':rcv.id, 'to':nid, 'lsa':lsa})
        logs.append(f"[{phase}] Processed {count} updates.")

    def _dijkstra(self, graph, start):
        d = {n: float('inf') for n in graph}
        d[start] = 0
        p = {n: None for n in graph}
        pq = [(0, start)]
        while pq:
            dist, u = heapq.heappop(pq)
            if dist > d.get(u, float('inf')): continue
            if u in graph:
                for v, w in graph[u].items():
                    if v not in d: d[v] = float('inf')
                    if d[u] + w < d[v]:
                        d[v] = d[u] + w
                        p[v] = u
                        heapq.heappush(pq, (d[v], v))
        return d, p

    def _get_nh(self, start, dest, parents):
        if dest not in parents or parents[dest] is None: return None
        curr = dest
        while parents[curr] != start:
            curr = parents[curr]
            if curr is None: return None
        return curr

    def _run_rip(self):
        logs = ["Starting RIP..."]
        for r in self.routers.values():
            r.distance_vector = {r.id:(0,'Local')}
            for n,c in self.get_neighbors(r.id): r.distance_vector[n]=(c,n)
        
        changed, i = True, 0
        while changed and i<20:
            changed, i = False, i+1
            for r in self.routers.values():
                for nid, cost in self.get_neighbors(r.id):
                    nv = self.routers[nid].distance_vector
                    for d, (m, _) in nv.items():
                        if cost+m < r.distance_vector.get(d,(INFINITY,None))[0]:
                            r.distance_vector[d] = (cost+m, nid)
                            changed=True
        
        for r in self.routers.values():
            for d, (c, nh) in r.distance_vector.items(): r.routing_table[d] = (nh, c)
        logs.append(f"RIP Converged in {i} steps.")
        return logs

    def _run_bgp(self):
        logs = ["Starting BGP..."]
        for r in self.routers.values():
            r.bgp_paths = {r.id:[r.id]}
            r.routing_table[r.id] = ("Local", "AS:[]")
        
        changed, i = True, 0
        while changed and i<20:
            changed, i = False, i+1
            for r in self.routers.values():
                for nid, _ in self.get_neighbors(r.id):
                    np = self.routers[nid].bgp_paths
                    for d, path in np.items():
                        if r.id in path: continue
                        newp = [r.id]+path
                        curr = r.bgp_paths.get(d)
                        if not curr or len(newp) < len(curr):
                            r.bgp_paths[d] = newp
                            r.routing_table[d] = (nid, f"Len:{len(newp)}")
                            changed=True
        logs.append(f"BGP Converged in {i} steps.")
        return logs