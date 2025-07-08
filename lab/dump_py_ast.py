import ast
import sys

class ASTDumper(ast.NodeVisitor):
    def __init__(self, indent_size=2):
        self.indent_level = 0
        self.indent_size = indent_size
        self.node_count = 0
        
    def _indent(self):
        return " " * (self.indent_level * self.indent_size)
    
    def _print_node(self, node, extra_info=""):
        self.node_count += 1
        node_name = node.__class__.__name__
        
        # Get node attributes (excluding child nodes)
        attrs = []
        for field, value in ast.iter_fields(node):
            if not isinstance(value, list) and not isinstance(value, ast.AST):
                attrs.append(f"{field}={repr(value)}")
        
        attr_str = f"({', '.join(attrs)})" if attrs else ""
        print(f"{self._indent()}{node_name}{attr_str}{extra_info}")
    
    def visit(self, node):
        """Override visit to add custom operations during traversal"""
        
        # Custom operations you can perform here:
        # 1. Count specific node types
        if isinstance(node, ast.FunctionDef):
            extra = f" [Function: {node.name}]"
        elif isinstance(node, ast.ClassDef):
            extra = f" [Class: {node.name}]"
        elif isinstance(node, ast.Name):
            extra = f" [Variable: {node.id}]"
        elif isinstance(node, ast.Constant):
            extra = f" [Value: {repr(node.value)}]"
        else:
            extra = ""
        
        self._print_node(node, extra)
        
        # Increment indent for children
        self.indent_level += 1
        
        # Visit all child nodes
        self.generic_visit(node)
        
        # Decrement indent after visiting children
        self.indent_level -= 1
    
    def get_stats(self):
        return f"Total nodes visited: {self.node_count}"

class DetailedASTAnalyzer(ast.NodeVisitor):
    """More advanced analyzer that collects statistics during traversal"""
    
    def __init__(self):
        self.stats = {
            'functions': [],
            'classes': [],
            'variables': set(),
            'imports': [],
            'node_counts': {},
            'complexity': 0
        }
        self.indent_level = 0
    
    def _indent(self):
        return "  " * self.indent_level
    
    def _count_node(self, node):
        node_type = node.__class__.__name__
        self.stats['node_counts'][node_type] = self.stats['node_counts'].get(node_type, 0) + 1
    
    def visit(self, node):
        self._count_node(node)
        
        # Print the node
        print(f"{self._indent()}{node.__class__.__name__}", end="")
        
        # Add specific information based on node type
        if isinstance(node, ast.FunctionDef):
            self.stats['functions'].append(node.name)
            args = [arg.arg for arg in node.args.args]
            print(f" '{node.name}' (args: {args})")
            
        elif isinstance(node, ast.ClassDef):
            self.stats['classes'].append(node.name)
            bases = [base.id if isinstance(base, ast.Name) else str(base) for base in node.bases]
            print(f" '{node.name}' (bases: {bases})")
            
        elif isinstance(node, ast.Name):
            self.stats['variables'].add(node.id)
            print(f" '{node.id}' (ctx: {node.ctx.__class__.__name__})")
            
        elif isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
            self.stats['imports'].extend(names)
            print(f" {names}")
            
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            names = [alias.name for alias in node.names]
            self.stats['imports'].append(f"{module}.{names}")
            print(f" from {module} import {names}")
            
        elif isinstance(node, ast.Constant):
            print(f" {repr(node.value)}")
            
        elif isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
            self.stats['complexity'] += 1
            print()
            
        else:
            print()
        
        # Traverse children
        self.indent_level += 1
        self.generic_visit(node)
        self.indent_level -= 1
    
    def print_summary(self):
        print("\n" + "="*50)
        print("AST ANALYSIS SUMMARY")
        print("="*50)
        
        print(f"Functions found: {len(self.stats['functions'])}")
        for func in self.stats['functions']:
            print(f"  - {func}")
        
        print(f"\nClasses found: {len(self.stats['classes'])}")
        for cls in self.stats['classes']:
            print(f"  - {cls}")
        
        print(f"\nUnique variables: {len(self.stats['variables'])}")
        for var in sorted(self.stats['variables']):
            print(f"  - {var}")
        
        print(f"\nImports: {len(self.stats['imports'])}")
        for imp in self.stats['imports']:
            print(f"  - {imp}")
        
        print(f"\nCyclomatic complexity indicators: {self.stats['complexity']}")
        
        print(f"\nNode type counts:")
        for node_type, count in sorted(self.stats['node_counts'].items()):
            print(f"  {node_type}: {count}")

def dump_ast_from_file(filename, analyzer_type="simple"):
    """Read a Python file and dump its AST with traversal"""
    try:
        with open(filename, 'r') as file:
            code = file.read()
        
        tree = ast.parse(code, filename=filename)
        print(f"AST traversal for file: {filename}")
        print("=" * 50)
        
        if analyzer_type == "detailed":
            analyzer = DetailedASTAnalyzer()
        else:
            analyzer = ASTDumper()
        
        analyzer.visit(tree)
        
        if hasattr(analyzer, 'print_summary'):
            analyzer.print_summary()
        elif hasattr(analyzer, 'get_stats'):
            print(f"\n{analyzer.get_stats()}")
        
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
    except SyntaxError as e:
        print(f"Syntax error in file '{filename}': {e}")

def dump_ast_from_string(code_string, analyzer_type="simple"):
    """Parse a code string and dump its AST with traversal"""
    try:
        tree = ast.parse(code_string)
        print("AST traversal for provided code:")
        print("=" * 30)
        
        if analyzer_type == "detailed":
            analyzer = DetailedASTAnalyzer()
        else:
            analyzer = ASTDumper()
        
        analyzer.visit(tree)
        
        if hasattr(analyzer, 'print_summary'):
            analyzer.print_summary()
        elif hasattr(analyzer, 'get_stats'):
            print(f"\n{analyzer.get_stats()}")
        
    except SyntaxError as e:
        print(f"Syntax error in code: {e}")

def main():
    analyzer_type = "simple"
    filename = None
    
    # Parse command line arguments
    args = sys.argv[1:]
    if "--detailed" in args:
        analyzer_type = "detailed"
        args.remove("--detailed")
    
    if args:
        filename = args[0]
        dump_ast_from_file(filename, analyzer_type)
    else:
        # Interactive mode
        print("Enter Python code (press Ctrl+D or Ctrl+Z when done):")
        print("Use --detailed flag for detailed analysis")
        try:
            code = sys.stdin.read()
            if code.strip():
                dump_ast_from_string(code, analyzer_type)
            else:
                print("No code provided")
        except KeyboardInterrupt:
            print("\nOperation cancelled")

if __name__ == "__main__":
    main()
