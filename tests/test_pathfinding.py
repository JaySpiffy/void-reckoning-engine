import pytest
from unittest.mock import MagicMock
from src.services.pathfinding_service import PathfindingService

# --- Mock Graph Elements ---

class MockEdge:
    def __init__(self, target, distance=10, blocked=False, traversable=True):
        self.target = target
        self.distance = distance
        self.blocked = blocked
        self._traversable = traversable
        
    def is_traversable(self):
        return self._traversable and not self.blocked

class MockNode:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.edges = []
        
    def add_edge(self, target, distance=10, blocked=False):
        edge = MockEdge(target, distance, blocked)
        self.edges.append(edge)
        return edge
        
    # Orderable for heap comparisons if cost is equal
    def __lt__(self, other):
        return self.id < other.id

# --- Fixtures ---

@pytest.fixture
def pf_service():
    return PathfindingService()

@pytest.fixture
def simple_graph():
    # A --(10)--> B --(10)--> C
    a = MockNode(1, "A")
    b = MockNode(2, "B")
    c = MockNode(3, "C")
    
    a.add_edge(b, 10)
    b.add_edge(c, 10)
    
    return {"A": a, "B": b, "C": c}

@pytest.fixture
def branching_graph():
    # A -> B (10) -> D (10) = 20
    # A -> C (50) -> D (10) = 60
    a = MockNode(1, "A")
    b = MockNode(2, "B")
    c = MockNode(3, "C")
    d = MockNode(4, "D")
    
    a.add_edge(b, 10)
    b.add_edge(d, 10)
    
    a.add_edge(c, 50)
    c.add_edge(d, 10)
    
    return {"A": a, "B": b, "C": c, "D": d}

# --- Tests ---

def test_same_node_path(pf_service, simple_graph):
    a = simple_graph["A"]
    path, cost, meta = pf_service.find_path(a, a)
    assert path == [a]
    assert cost == 0

def test_basic_path(pf_service, simple_graph):
    a = simple_graph["A"]
    c = simple_graph["C"]
    
    path, cost, meta = pf_service.find_path(a, c)
    
    assert cost == 20
    assert len(path) == 3
    assert path[0] == a
    assert path[2] == c

def test_shortest_path_selection(pf_service, branching_graph):
    a = branching_graph["A"]
    d = branching_graph["D"]
    
    path, cost, meta = pf_service.find_path(a, d)
    
    # Should pick A->B->D (Cost 20) over A->C->D (Cost 60)
    assert cost == 20
    assert branching_graph["B"] in path
    assert branching_graph["C"] not in path

def test_blocked_edge_avoidance(pf_service, branching_graph):
    a = branching_graph["A"]
    b = branching_graph["B"]
    c = branching_graph["C"]
    d = branching_graph["D"]
    
    # Block the cheap path (A->B)
    edge = a.edges[0] # To B
    assert edge.target == b
    edge.blocked = True
    
    path, cost, meta = pf_service.find_path(a, d)
    
    # Should now pick A->C->D (Cost 60)
    assert cost == 60
    assert c in path
    assert b not in path

def test_no_path_found(pf_service):
    a = MockNode(1, "A")
    b = MockNode(2, "B")
    # No edges
    
    path, cost, meta = pf_service.find_path(a, b)
    
    assert path is None
    assert cost == float('inf')

def test_path_caching(pf_service, simple_graph):
    a = simple_graph["A"]
    b = simple_graph["B"]
    
    # First call
    p1, c1, m1 = pf_service.find_cached_path(a, b)
    assert (a, b, None) in pf_service._path_cache
    
    # Modify graph (Should NOT affect cached result)
    a.edges[0].distance = 1000
    
    # Second call - verify cache hit
    p2, c2, m2 = pf_service.find_cached_path(a, b)
    assert c2 == 10 # Old cost
    
    # Clear cache
    pf_service.clear_cache()
    
    # Third call - verify re-calculation
    p3, c3, m3 = pf_service.find_cached_path(a, b)
    assert c3 == 1000 # New cost
