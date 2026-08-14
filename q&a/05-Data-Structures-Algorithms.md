---
title: Data Structures and Algorithms
aliases: [DSA, Data Structures and Algorithms]
tags: [algorithms, data-structures, interview]
order: 5
---

# Data Structures and Algorithms Interview Q&A

> [!info]+ Related Notes
> [[04-CSharp-Fundamentals|C# Fundamentals]] · [[16-System-Design|System Design]]

## Fundamental Concepts

### 1. What is a data structure?
A data structure is a way of organizing, managing, and storing data to enable efficient access and modification. It defines the relationship between data elements and the operations that can be performed on them.

### 2. What is an algorithm?
An algorithm is a step-by-step procedure or set of rules to solve a specific problem or perform a computation. It takes an input, processes it, and produces an output.

### 3. What is time complexity?
Time complexity measures the amount of time an algorithm takes to complete as a function of input size (n). Expressed using Big O notation.

**Common complexities (best to worst):**
- O(1) - Constant
- O(log n) - Logarithmic
- O(n) - Linear
- O(n log n) - Linearithmic
- O(n²) - Quadratic
- O(n³) - Cubic
- O(2ⁿ) - Exponential
- O(n!) - Factorial

### 4. What is space complexity?
Space complexity measures the amount of memory an algorithm uses relative to input size. Includes both auxiliary space and input space.

### 5. What is Big O notation?
Mathematical notation describing the upper bound (worst-case) of an algorithm's time or space complexity as input size approaches infinity.

**Examples:**
```csharp
// O(1) - Constant
int GetFirst(int[] arr) => arr[0];

// O(n) - Linear
int Sum(int[] arr) {
    int sum = 0;
    foreach(int num in arr) sum += num;
    return sum;
}

// O(n²) - Quadratic
void PrintPairs(int[] arr) {
    for(int i = 0; i < arr.Length; i++)
        for(int j = 0; j < arr.Length; j++)
            Console.WriteLine($"{arr[i]}, {arr[j]}");
}
```

## Arrays

### 6. What is an array?
A fixed-size, contiguous collection of elements of the same type, stored in sequential memory locations. Random access with O(1) time.

**Pros:**
- Fast random access: O(1)
- Cache-friendly (contiguous memory)
- Simple to use

**Cons:**
- Fixed size
- Expensive insertion/deletion: O(n)
- Wasted space if not fully used

### 7. What is a dynamic array (List)?
A resizable array that grows automatically when capacity is exceeded.

```csharp
List<int> list = new List<int>(); // Initial capacity 4
list.Add(1); // O(1) amortized
list.Add(2);
list.Insert(0, 5); // O(n)
list.RemoveAt(1); // O(n)
```

**Time Complexity:**
- Access: O(1)
- Search: O(n)
- Insert at end: O(1) amortized
- Insert at position: O(n)
- Delete: O(n)

### 8. How does array resizing work?
When capacity is reached, a new array (usually 2x size) is allocated, elements are copied, and old array is discarded.

```csharp
// Internal behavior
if (count == capacity) {
    capacity *= 2;
    int[] newArray = new int[capacity];
    Array.Copy(oldArray, newArray, count);
}
```

## Linked Lists

### 9. What is a linked list?
A linear data structure where elements (nodes) are connected via pointers. Each node contains data and reference(s) to next/previous nodes.

```csharp
public class Node {
    public int Data { get; set; }
    public Node Next { get; set; }
}

public class LinkedList {
    public Node Head { get; set; }
    
    public void AddFirst(int data) {
        Node newNode = new Node { Data = data, Next = Head };
        Head = newNode;
    }
}
```

### 10. What are the types of linked lists?

**Singly Linked List:**
- Each node points to next node only
- Traverse in one direction

**Doubly Linked List:**
- Each node has pointers to both next and previous
- Traverse in both directions

```csharp
public class DoublyNode {
    public int Data { get; set; }
    public DoublyNode Next { get; set; }
    public DoublyNode Prev { get; set; }
}
```

**Circular Linked List:**
- Last node points back to first node
- No null references

### 11. Array vs Linked List - when to use which?

**Use Array when:**
- Random access needed frequently
- Size is known/fixed
- Memory is contiguous
- Cache performance matters

**Use Linked List when:**
- Frequent insertions/deletions at beginning/middle
- Size is unknown/dynamic
- No random access needed
- Memory fragmentation acceptable

### 12. How do you detect a cycle in a linked list?

**Floyd's Cycle Detection (Tortoise and Hare):**
```csharp
public bool HasCycle(Node head) {
    if (head == null) return false;
    
    Node slow = head;
    Node fast = head;
    
    while (fast != null && fast.Next != null) {
        slow = slow.Next;
        fast = fast.Next.Next;
        
        if (slow == fast) return true;
    }
    
    return false;
}
```
**Time:** O(n), **Space:** O(1)

### 13. How do you reverse a linked list?

```csharp
public Node Reverse(Node head) {
    Node prev = null;
    Node current = head;
    
    while (current != null) {
        Node next = current.Next;
        current.Next = prev;
        prev = current;
        current = next;
    }
    
    return prev;
}
```
**Time:** O(n), **Space:** O(1)

## Stacks

### 14. What is a stack?
A LIFO (Last In First Out) data structure where elements are added and removed from the same end (top).

**Operations:**
- Push: Add element - O(1)
- Pop: Remove element - O(1)
- Peek: View top element - O(1)

```csharp
Stack<int> stack = new Stack<int>();
stack.Push(1);
stack.Push(2);
int top = stack.Peek(); // 2
int popped = stack.Pop(); // 2
```

### 15. What are common stack applications?

- Function call management (call stack)
- Undo/Redo operations
- Expression evaluation (postfix, infix)
- Backtracking algorithms
- Browser history
- Balanced parentheses checking

**Example - Balanced Parentheses:**
```csharp
public bool IsValid(string s) {
    Stack<char> stack = new Stack<char>();
    Dictionary<char, char> pairs = new Dictionary<char, char> {
        {')', '('}, {']', '['}, {'}', '{'}
    };
    
    foreach (char c in s) {
        if (c == '(' || c == '[' || c == '{') {
            stack.Push(c);
        } else {
            if (stack.Count == 0 || stack.Pop() != pairs[c])
                return false;
        }
    }
    
    return stack.Count == 0;
}
```

## Queues

### 16. What is a queue?
A FIFO (First In First Out) data structure where elements are added at rear and removed from front.

**Operations:**
- Enqueue: Add at rear - O(1)
- Dequeue: Remove from front - O(1)
- Peek: View front element - O(1)

```csharp
Queue<int> queue = new Queue<int>();
queue.Enqueue(1);
queue.Enqueue(2);
int front = queue.Peek(); // 1
int dequeued = queue.Dequeue(); // 1
```

### 17. What is a circular queue?
A queue with fixed size where rear wraps around to beginning when end is reached, efficiently using space.

```csharp
public class CircularQueue {
    private int[] array;
    private int front, rear, size, capacity;
    
    public CircularQueue(int k) {
        capacity = k;
        array = new int[k];
        front = 0;
        rear = -1;
        size = 0;
    }
    
    public bool Enqueue(int value) {
        if (size == capacity) return false;
        rear = (rear + 1) % capacity;
        array[rear] = value;
        size++;
        return true;
    }
    
    public bool Dequeue() {
        if (size == 0) return false;
        front = (front + 1) % capacity;
        size--;
        return true;
    }
}
```

### 18. What is a priority queue?
A queue where elements have priorities and are dequeued based on priority rather than insertion order. Usually implemented with heap.

```csharp
// Min heap (smallest value has highest priority)
PriorityQueue<int, int> pq = new PriorityQueue<int, int>();
pq.Enqueue(5, 5);
pq.Enqueue(1, 1);
pq.Enqueue(3, 3);
int min = pq.Dequeue(); // 1
```

## Hash Tables

### 19. What is a hash table?
A data structure that maps keys to values using a hash function. Provides average O(1) time for insert, delete, and search.

```csharp
Dictionary<string, int> dict = new Dictionary<string, int>();
dict["apple"] = 5; // O(1)
int count = dict["apple"]; // O(1)
bool exists = dict.ContainsKey("banana"); // O(1)
```

### 20. How does a hash function work?
Converts a key into an array index. Good hash functions:
- Deterministic (same input → same output)
- Uniform distribution
- Fast to compute
- Minimize collisions

**Simple example:**
```csharp
int HashFunction(string key, int tableSize) {
    int hash = 0;
    foreach (char c in key) {
        hash = (hash * 31 + c) % tableSize;
    }
    return hash;
}
```

### 21. What are hash collisions and how are they resolved?

**Collision:** When two keys hash to same index.

**Resolution methods:**

**1. Chaining:**
Each bucket contains a linked list of entries.
```csharp
class HashTable {
    private LinkedList<KeyValuePair<string, int>>[] buckets;
    
    public void Put(string key, int value) {
        int index = GetHash(key);
        if (buckets[index] == null)
            buckets[index] = new LinkedList<KeyValuePair<string, int>>();
        
        // Add or update in linked list
        buckets[index].AddLast(new KeyValuePair<string, int>(key, value));
    }
}
```

**2. Open Addressing:**
Find next available slot using probing:
- Linear probing: Try index+1, index+2, ...
- Quadratic probing: Try index+1², index+2², ...
- Double hashing: Use second hash function

### 22. When should you use a hash table vs array?

**Use Hash Table when:**
- Need key-value associations
- Fast lookup by key required
- Keys are non-sequential
- O(1) average time critical

**Use Array when:**
- Sequential integer indices
- Cache locality important
- Predictable memory usage
- Ordered iteration needed

## Trees

### 23. What is a tree?
A hierarchical data structure with a root node and child nodes, forming parent-child relationships. No cycles allowed.

**Terminology:**
- **Root:** Top node with no parent
- **Leaf:** Node with no children
- **Height:** Longest path from root to leaf
- **Depth:** Distance from root to node
- **Subtree:** Tree formed by node and descendants

### 24. What is a binary tree?
A tree where each node has at most two children (left and right).

```csharp
public class TreeNode {
    public int Value { get; set; }
    public TreeNode Left { get; set; }
    public TreeNode Right { get; set; }
}
```

### 25. What are tree traversal methods?

**Depth-First Search (DFS):**

**Inorder (Left-Root-Right):**
```csharp
void Inorder(TreeNode node) {
    if (node == null) return;
    Inorder(node.Left);
    Console.WriteLine(node.Value);
    Inorder(node.Right);
}
```

**Preorder (Root-Left-Right):**
```csharp
void Preorder(TreeNode node) {
    if (node == null) return;
    Console.WriteLine(node.Value);
    Preorder(node.Left);
    Preorder(node.Right);
}
```

**Postorder (Left-Right-Root):**
```csharp
void Postorder(TreeNode node) {
    if (node == null) return;
    Postorder(node.Left);
    Postorder(node.Right);
    Console.WriteLine(node.Value);
}
```

**Breadth-First Search (BFS/Level-Order):**
```csharp
void LevelOrder(TreeNode root) {
    if (root == null) return;
    
    Queue<TreeNode> queue = new Queue<TreeNode>();
    queue.Enqueue(root);
    
    while (queue.Count > 0) {
        TreeNode node = queue.Dequeue();
        Console.WriteLine(node.Value);
        
        if (node.Left != null) queue.Enqueue(node.Left);
        if (node.Right != null) queue.Enqueue(node.Right);
    }
}
```

### 26. What is a Binary Search Tree (BST)?
A binary tree where for each node:
- Left subtree contains only smaller values
- Right subtree contains only larger values
- Both subtrees are also BSTs

**Operations (average case):**
- Search: O(log n)
- Insert: O(log n)
- Delete: O(log n)

```csharp
TreeNode Search(TreeNode root, int target) {
    if (root == null || root.Value == target)
        return root;
    
    if (target < root.Value)
        return Search(root.Left, target);
    else
        return Search(root.Right, target);
}

TreeNode Insert(TreeNode root, int value) {
    if (root == null)
        return new TreeNode { Value = value };
    
    if (value < root.Value)
        root.Left = Insert(root.Left, value);
    else if (value > root.Value)
        root.Right = Insert(root.Right, value);
    
    return root;
}
```

### 27. What is a balanced tree?
A tree where the height difference between left and right subtrees of any node is at most 1. Ensures O(log n) operations.

**Examples:**
- AVL Tree
- Red-Black Tree
- B-Tree

### 28. What is an AVL Tree?
A self-balancing BST where the balance factor (height difference between left and right subtrees) is always -1, 0, or 1.

**Rotations:**
- Left Rotation
- Right Rotation
- Left-Right Rotation
- Right-Left Rotation

### 29. What is a heap?
A complete binary tree satisfying heap property:
- **Max Heap:** Parent ≥ children
- **Min Heap:** Parent ≤ children

**Operations:**
- Insert: O(log n)
- Extract min/max: O(log n)
- Peek min/max: O(1)

```csharp
// Min Heap implementation
public class MinHeap {
    private List<int> heap = new List<int>();
    
    public void Insert(int value) {
        heap.Add(value);
        HeapifyUp(heap.Count - 1);
    }
    
    public int ExtractMin() {
        if (heap.Count == 0) throw new InvalidOperationException();
        
        int min = heap[0];
        heap[0] = heap[heap.Count - 1];
        heap.RemoveAt(heap.Count - 1);
        HeapifyDown(0);
        return min;
    }
    
    private void HeapifyUp(int index) {
        while (index > 0) {
            int parent = (index - 1) / 2;
            if (heap[index] >= heap[parent]) break;
            
            Swap(index, parent);
            index = parent;
        }
    }
    
    private void HeapifyDown(int index) {
        while (true) {
            int left = 2 * index + 1;
            int right = 2 * index + 2;
            int smallest = index;
            
            if (left < heap.Count && heap[left] < heap[smallest])
                smallest = left;
            if (right < heap.Count && heap[right] < heap[smallest])
                smallest = right;
            
            if (smallest == index) break;
            
            Swap(index, smallest);
            index = smallest;
        }
    }
    
    private void Swap(int i, int j) {
        int temp = heap[i];
        heap[i] = heap[j];
        heap[j] = temp;
    }
}
```

### 30. What is a Trie (Prefix Tree)?
A tree used for storing strings where each node represents a character. Efficient for prefix-based operations.

```csharp
public class TrieNode {
    public Dictionary<char, TrieNode> Children = new Dictionary<char, TrieNode>();
    public bool IsEndOfWord;
}

public class Trie {
    private TrieNode root = new TrieNode();
    
    public void Insert(string word) {
        TrieNode node = root;
        foreach (char c in word) {
            if (!node.Children.ContainsKey(c))
                node.Children[c] = new TrieNode();
            node = node.Children[c];
        }
        node.IsEndOfWord = true;
    }
    
    public bool Search(string word) {
        TrieNode node = root;
        foreach (char c in word) {
            if (!node.Children.ContainsKey(c))
                return false;
            node = node.Children[c];
        }
        return node.IsEndOfWord;
    }
    
    public bool StartsWith(string prefix) {
        TrieNode node = root;
        foreach (char c in prefix) {
            if (!node.Children.ContainsKey(c))
                return false;
            node = node.Children[c];
        }
        return true;
    }
}
```

**Time Complexity:** O(m) where m is string length
**Use Cases:** Autocomplete, spell checker, IP routing

## Graphs

### 31. What is a graph?
A collection of nodes (vertices) connected by edges. Can be directed or undirected, weighted or unweighted.

**Representations:**

**Adjacency Matrix:**
```csharp
int[,] graph = new int[V, V]; // V = number of vertices
graph[0, 1] = 1; // Edge from 0 to 1
```
**Space:** O(V²), **Edge check:** O(1)

**Adjacency List:**
```csharp
List<int>[] graph = new List<int>[V];
for (int i = 0; i < V; i++)
    graph[i] = new List<int>();
graph[0].Add(1); // Edge from 0 to 1
```
**Space:** O(V + E), **Edge check:** O(degree)

### 32. What is DFS (Depth-First Search)?
Explores as far as possible along each branch before backtracking. Uses stack (or recursion).

```csharp
void DFS(List<int>[] graph, int start) {
    bool[] visited = new bool[graph.Length];
    DFSUtil(graph, start, visited);
}

void DFSUtil(List<int>[] graph, int node, bool[] visited) {
    visited[node] = true;
    Console.WriteLine(node);
    
    foreach (int neighbor in graph[node]) {
        if (!visited[neighbor])
            DFSUtil(graph, neighbor, visited);
    }
}
```
**Time:** O(V + E), **Space:** O(V)

### 33. What is BFS (Breadth-First Search)?
Explores all neighbors at current depth before moving to next level. Uses queue.

```csharp
void BFS(List<int>[] graph, int start) {
    bool[] visited = new bool[graph.Length];
    Queue<int> queue = new Queue<int>();
    
    visited[start] = true;
    queue.Enqueue(start);
    
    while (queue.Count > 0) {
        int node = queue.Dequeue();
        Console.WriteLine(node);
        
        foreach (int neighbor in graph[node]) {
            if (!visited[neighbor]) {
                visited[neighbor] = true;
                queue.Enqueue(neighbor);
            }
        }
    }
}
```
**Time:** O(V + E), **Space:** O(V)

### 34. When to use DFS vs BFS?

**Use DFS when:**
- Finding path between two nodes
- Detecting cycles
- Topological sorting
- Connected components
- Memory is limited (less space than BFS)

**Use BFS when:**
- Shortest path in unweighted graph
- Finding all nodes within k distance
- Level-order traversal
- Finding if path exists

### 35. What is Dijkstra's algorithm?
Finds shortest path from source to all other vertices in weighted graph with non-negative weights.

```csharp
int[] Dijkstra(List<(int node, int weight)>[] graph, int start) {
    int n = graph.Length;
    int[] distances = new int[n];
    Array.Fill(distances, int.MaxValue);
    distances[start] = 0;
    
    PriorityQueue<(int dist, int node), int> pq = new PriorityQueue<(int, int), int>();
    pq.Enqueue((0, start), 0);
    
    while (pq.Count > 0) {
        var (dist, node) = pq.Dequeue();
        
        if (dist > distances[node]) continue;
        
        foreach (var (neighbor, weight) in graph[node]) {
            int newDist = dist + weight;
            if (newDist < distances[neighbor]) {
                distances[neighbor] = newDist;
                pq.Enqueue((newDist, neighbor), newDist);
            }
        }
    }
    
    return distances;
}
```
**Time:** O((V + E) log V) with priority queue

### 36. What is a topological sort?
Linear ordering of vertices in directed acyclic graph (DAG) where for every edge u→v, u comes before v.

```csharp
List<int> TopologicalSort(List<int>[] graph) {
    int n = graph.Length;
    int[] inDegree = new int[n];
    
    // Calculate in-degrees
    for (int i = 0; i < n; i++)
        foreach (int neighbor in graph[i])
            inDegree[neighbor]++;
    
    // Add all vertices with in-degree 0
    Queue<int> queue = new Queue<int>();
    for (int i = 0; i < n; i++)
        if (inDegree[i] == 0)
            queue.Enqueue(i);
    
    List<int> result = new List<int>();
    while (queue.Count > 0) {
        int node = queue.Dequeue();
        result.Add(node);
        
        foreach (int neighbor in graph[node]) {
            inDegree[neighbor]--;
            if (inDegree[neighbor] == 0)
                queue.Enqueue(neighbor);
        }
    }
    
    return result.Count == n ? result : null; // null if cycle exists
}
```
**Time:** O(V + E)
**Use Cases:** Task scheduling, build systems, course prerequisites

## Sorting Algorithms

### 37. What is Bubble Sort?
Repeatedly swaps adjacent elements if they're in wrong order.

```csharp
void BubbleSort(int[] arr) {
    int n = arr.Length;
    for (int i = 0; i < n - 1; i++) {
        bool swapped = false;
        for (int j = 0; j < n - i - 1; j++) {
            if (arr[j] > arr[j + 1]) {
                Swap(ref arr[j], ref arr[j + 1]);
                swapped = true;
            }
        }
        if (!swapped) break; // Already sorted
    }
}
```
**Time:** O(n²), **Space:** O(1), **Stable:** Yes

### 38. What is Selection Sort?
Finds minimum element and places it at beginning.

```csharp
void SelectionSort(int[] arr) {
    int n = arr.Length;
    for (int i = 0; i < n - 1; i++) {
        int minIdx = i;
        for (int j = i + 1; j < n; j++) {
            if (arr[j] < arr[minIdx])
                minIdx = j;
        }
        Swap(ref arr[i], ref arr[minIdx]);
    }
}
```
**Time:** O(n²), **Space:** O(1), **Stable:** No

### 39. What is Insertion Sort?
Builds sorted array one element at a time by inserting elements in correct position.

```csharp
void InsertionSort(int[] arr) {
    for (int i = 1; i < arr.Length; i++) {
        int key = arr[i];
        int j = i - 1;
        
        while (j >= 0 && arr[j] > key) {
            arr[j + 1] = arr[j];
            j--;
        }
        arr[j + 1] = key;
    }
}
```
**Time:** O(n²), **Space:** O(1), **Stable:** Yes
**Good for:** Small arrays, nearly sorted data

### 40. What is Merge Sort?
Divide-and-conquer algorithm that divides array, sorts halves, and merges them.

```csharp
void MergeSort(int[] arr, int left, int right) {
    if (left < right) {
        int mid = left + (right - left) / 2;
        
        MergeSort(arr, left, mid);
        MergeSort(arr, mid + 1, right);
        Merge(arr, left, mid, right);
    }
}

void Merge(int[] arr, int left, int mid, int right) {
    int n1 = mid - left + 1;
    int n2 = right - mid;
    
    int[] L = new int[n1];
    int[] R = new int[n2];
    
    Array.Copy(arr, left, L, 0, n1);
    Array.Copy(arr, mid + 1, R, 0, n2);
    
    int i = 0, j = 0, k = left;
    
    while (i < n1 && j < n2) {
        if (L[i] <= R[j])
            arr[k++] = L[i++];
        else
            arr[k++] = R[j++];
    }
    
    while (i < n1) arr[k++] = L[i++];
    while (j < n2) arr[k++] = R[j++];
}
```
**Time:** O(n log n), **Space:** O(n), **Stable:** Yes

### 41. What is Quick Sort?
Divide-and-conquer using pivot element to partition array.

```csharp
void QuickSort(int[] arr, int low, int high) {
    if (low < high) {
        int pi = Partition(arr, low, high);
        QuickSort(arr, low, pi - 1);
        QuickSort(arr, pi + 1, high);
    }
}

int Partition(int[] arr, int low, int high) {
    int pivot = arr[high];
    int i = low - 1;
    
    for (int j = low; j < high; j++) {
        if (arr[j] < pivot) {
            i++;
            Swap(ref arr[i], ref arr[j]);
        }
    }
    
    Swap(ref arr[i + 1], ref arr[high]);
    return i + 1;
}
```
**Time:** O(n log n) average, O(n²) worst, **Space:** O(log n), **Stable:** No

### 42. What is Heap Sort?
Uses binary heap to sort elements.

```csharp
void HeapSort(int[] arr) {
    int n = arr.Length;
    
    // Build max heap
    for (int i = n / 2 - 1; i >= 0; i--)
        Heapify(arr, n, i);
    
    // Extract elements from heap
    for (int i = n - 1; i > 0; i--) {
        Swap(ref arr[0], ref arr[i]);
        Heapify(arr, i, 0);
    }
}

void Heapify(int[] arr, int n, int i) {
    int largest = i;
    int left = 2 * i + 1;
    int right = 2 * i + 2;
    
    if (left < n && arr[left] > arr[largest])
        largest = left;
    if (right < n && arr[right] > arr[largest])
        largest = right;
    
    if (largest != i) {
        Swap(ref arr[i], ref arr[largest]);
        Heapify(arr, n, largest);
    }
}
```
**Time:** O(n log n), **Space:** O(1), **Stable:** No

### 43. Which sorting algorithm should you use?

**Quick Sort:** General purpose, average O(n log n)
**Merge Sort:** Need stability, worst-case O(n log n)
**Heap Sort:** Memory constrained, guaranteed O(n log n)
**Insertion Sort:** Small arrays, nearly sorted data
**Tim Sort:** Built-in (Array.Sort in .NET), hybrid of merge+insertion

## Searching Algorithms

### 44. What is Binary Search?
Searches sorted array by repeatedly dividing search interval in half.

```csharp
int BinarySearch(int[] arr, int target) {
    int left = 0, right = arr.Length - 1;
    
    while (left <= right) {
        int mid = left + (right - left) / 2;
        
        if (arr[mid] == target)
            return mid;
        else if (arr[mid] < target)
            left = mid + 1;
        else
            right = mid - 1;
    }
    
    return -1; // Not found
}
```
**Time:** O(log n), **Space:** O(1)
**Requirement:** Array must be sorted

### 45. What is Binary Search on rotated array?

```csharp
int SearchRotated(int[] nums, int target) {
    int left = 0, right = nums.Length - 1;
    
    while (left <= right) {
        int mid = left + (right - left) / 2;
        
        if (nums[mid] == target)
            return mid;
        
        // Left half is sorted
        if (nums[left] <= nums[mid]) {
            if (target >= nums[left] && target < nums[mid])
                right = mid - 1;
            else
                left = mid + 1;
        }
        // Right half is sorted
        else {
            if (target > nums[mid] && target <= nums[right])
                left = mid + 1;
            else
                right = mid - 1;
        }
    }
    
    return -1;
}
```

## Dynamic Programming

### 46. What is Dynamic Programming?
Optimization technique that solves complex problems by breaking them into simpler subproblems and storing results to avoid redundant calculations.

**Two approaches:**
1. **Memoization (Top-Down):** Recursion + caching
2. **Tabulation (Bottom-Up):** Iterative + table

### 47. What is the Fibonacci sequence with DP?

**Naive Recursion - O(2ⁿ):**
```csharp
int Fib(int n) {
    if (n <= 1) return n;
    return Fib(n - 1) + Fib(n - 2);
}
```

**Memoization - O(n):**
```csharp
int Fib(int n, Dictionary<int, int> memo = null) {
    memo ??= new Dictionary<int, int>();
    
    if (n <= 1) return n;
    if (memo.ContainsKey(n)) return memo[n];
    
    memo[n] = Fib(n - 1, memo) + Fib(n - 2, memo);
    return memo[n];
}
```

**Tabulation - O(n), O(1) space:**
```csharp
int Fib(int n) {
    if (n <= 1) return n;
    
    int prev2 = 0, prev1 = 1;
    for (int i = 2; i <= n; i++) {
        int current = prev1 + prev2;
        prev2 = prev1;
        prev1 = current;
    }
    return prev1;
}
```

### 48. What is the Knapsack problem?
Given weights and values of items, maximize value without exceeding capacity.

```csharp
int Knapsack(int[] weights, int[] values, int capacity) {
    int n = weights.Length;
    int[,] dp = new int[n + 1, capacity + 1];
    
    for (int i = 1; i <= n; i++) {
        for (int w = 1; w <= capacity; w++) {
            if (weights[i - 1] <= w) {
                dp[i, w] = Math.Max(
                    values[i - 1] + dp[i - 1, w - weights[i - 1]],
                    dp[i - 1, w]
                );
            } else {
                dp[i, w] = dp[i - 1, w];
            }
        }
    }
    
    return dp[n, capacity];
}
```
**Time:** O(n × capacity), **Space:** O(n × capacity)

### 49. What is Longest Common Subsequence?

```csharp
int LCS(string text1, string text2) {
    int m = text1.Length, n = text2.Length;
    int[,] dp = new int[m + 1, n + 1];
    
    for (int i = 1; i <= m; i++) {
        for (int j = 1; j <= n; j++) {
            if (text1[i - 1] == text2[j - 1])
                dp[i, j] = dp[i - 1, j - 1] + 1;
            else
                dp[i, j] = Math.Max(dp[i - 1, j], dp[i, j - 1]);
        }
    }
    
    return dp[m, n];
}
```

### 50. What is the Coin Change problem?

```csharp
int CoinChange(int[] coins, int amount) {
    int[] dp = new int[amount + 1];
    Array.Fill(dp, amount + 1);
    dp[0] = 0;
    
    for (int i = 1; i <= amount; i++) {
        foreach (int coin in coins) {
            if (coin <= i) {
                dp[i] = Math.Min(dp[i], dp[i - coin] + 1);
            }
        }
    }
    
    return dp[amount] > amount ? -1 : dp[amount];
}
```

## Advanced Topics

### 51. What is two pointers technique?

```csharp
// Two Sum in sorted array
int[] TwoSum(int[] nums, int target) {
    int left = 0, right = nums.Length - 1;
    
    while (left < right) {
        int sum = nums[left] + nums[right];
        if (sum == target)
            return new int[] { left, right };
        else if (sum < target)
            left++;
        else
            right--;
    }
    
    return new int[] { -1, -1 };
}
```

### 52. What is sliding window technique?

```csharp
// Maximum sum subarray of size k
int MaxSum(int[] arr, int k) {
    int maxSum = 0, windowSum = 0;
    
    // First window
    for (int i = 0; i < k; i++)
        windowSum += arr[i];
    maxSum = windowSum;
    
    // Slide window
    for (int i = k; i < arr.Length; i++) {
        windowSum = windowSum - arr[i - k] + arr[i];
        maxSum = Math.Max(maxSum, windowSum);
    }
    
    return maxSum;
}
```

### 53. What is backtracking?
Incrementally builds candidates and abandons candidates that fail constraints.

```csharp
// N-Queens problem
void SolveNQueens(int n) {
    List<List<string>> result = new List<List<string>>();
    char[][] board = new char[n][];
    for (int i = 0; i < n; i++) {
        board[i] = new char[n];
        Array.Fill(board[i], '.');
    }
    
    Backtrack(board, 0, result);
}

void Backtrack(char[][] board, int row, List<List<string>> result) {
    if (row == board.Length) {
        result.Add(ConstructSolution(board));
        return;
    }
    
    for (int col = 0; col < board.Length; col++) {
        if (IsSafe(board, row, col)) {
            board[row][col] = 'Q';
            Backtrack(board, row + 1, result);
            board[row][col] = '.'; // Backtrack
        }
    }
}
```

### 54. What is greedy algorithm?
Makes locally optimal choice at each step, hoping to find global optimum.

```csharp
// Activity Selection
List<int> ActivitySelection(int[] start, int[] finish) {
    List<int> result = new List<int>();
    int n = start.Length;
    
    // Sort by finish time
    var activities = Enumerable.Range(0, n)
        .OrderBy(i => finish[i])
        .ToList();
    
    result.Add(activities[0]);
    int lastFinish = finish[activities[0]];
    
    for (int i = 1; i < n; i++) {
        int idx = activities[i];
        if (start[idx] >= lastFinish) {
            result.Add(idx);
            lastFinish = finish[idx];
        }
    }
    
    return result;
}
```

### 55. What is bit manipulation?

**Common operations:**
```csharp
// Check if kth bit is set
bool IsBitSet(int n, int k) => (n & (1 << k)) != 0;

// Set kth bit
int SetBit(int n, int k) => n | (1 << k);

// Clear kth bit
int ClearBit(int n, int k) => n & ~(1 << k);

// Toggle kth bit
int ToggleBit(int n, int k) => n ^ (1 << k);

// Count set bits
int CountSetBits(int n) {
    int count = 0;
    while (n > 0) {
        count += n & 1;
        n >>= 1;
    }
    return count;
}

// Check if power of 2
bool IsPowerOfTwo(int n) => n > 0 && (n & (n - 1)) == 0;
```

## Problem-Solving Strategies

### 56. How do you approach algorithm problems?

1. **Understand the problem:** Read carefully, ask clarifying questions
2. **Examples:** Work through examples manually
3. **Break down:** Identify subproblems
4. **Choose approach:** Brute force → optimize
5. **Data structures:** Pick appropriate DS
6. **Edge cases:** Consider null, empty, duplicates
7. **Test:** Verify with test cases
8. **Optimize:** Analyze time/space complexity

### 57. What are common problem patterns?

- **Two Pointers:** Sorted arrays, palindromes
- **Sliding Window:** Subarrays, substrings
- **Fast & Slow Pointers:** Cycle detection
- **Merge Intervals:** Overlapping intervals
- **Cyclic Sort:** Missing numbers in range
- **In-place LinkedList Reversal**
- **Tree BFS:** Level-order traversal
- **Tree DFS:** All paths, sum problems
- **Two Heaps:** Median finding
- **Subsets:** Combinations, permutations
- **Modified Binary Search:** Rotated arrays
- **Top K Elements:** Heap-based
- **K-way Merge:** Sorted lists
- **Dynamic Programming:** Optimization problems
- **Backtracking:** All solutions

### 58. How do you optimize an algorithm?

1. **Eliminate redundancy:** Cache repeated calculations
2. **Better data structure:** Hash for O(1) lookup
3. **Reduce iterations:** Two pointers, binary search
4. **Space-time tradeoff:** Use memory to save time
5. **Preprocessing:** Sort or precompute
6. **Mathematical insight:** Find formula
7. **Divide and conquer:** Break into subproblems

### 59. What are space-time tradeoffs?

**Example - Two Sum:**

**O(n²) time, O(1) space:**
```csharp
// Nested loops
```

**O(n) time, O(n) space:**
```csharp
int[] TwoSum(int[] nums, int target) {
    Dictionary<int, int> map = new Dictionary<int, int>();
    for (int i = 0; i < nums.Length; i++) {
        int complement = target - nums[i];
        if (map.ContainsKey(complement))
            return new int[] { map[complement], i };
        map[nums[i]] = i;
    }
    return null;
}
```

### 60. What are must-know algorithm interview problems?

**Arrays:**
- Two Sum
- Best Time to Buy/Sell Stock
- Product of Array Except Self
- Maximum Subarray (Kadane's)

**Strings:**
- Valid Anagram
- Longest Substring Without Repeating
- Valid Palindrome
- Group Anagrams

**Linked Lists:**
- Reverse Linked List
- Detect Cycle
- Merge Two Sorted Lists
- Remove Nth Node From End

**Trees:**
- Maximum Depth
- Validate BST
- Lowest Common Ancestor
- Serialize/Deserialize Tree

**Graphs:**
- Number of Islands
- Course Schedule
- Clone Graph
- Word Ladder

**Dynamic Programming:**
- Climbing Stairs
- Coin Change
- Longest Increasing Subsequence
- House Robber

**Misc:**
- Valid Parentheses
- Merge Intervals
- LRU Cache
- Top K Frequent Elements
