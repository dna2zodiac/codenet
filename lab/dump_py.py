import ast
import sys

class PythonParser:
    def __init__(self):
        self.python_version = sys.version_info.major
        self.scope_stack = []  # Track current scope
        self.symbol_table = {}  # Track variable assignments and their types
    
    def parse(self, code):
        """Parse Python code and return a tuple tree representation."""
        try:
            tree = ast.parse(code)
            self.scope_stack = []
            self.symbol_table = {}
            return self._visit_node(tree)
        except SyntaxError as e:
            raise ValueError(f"Invalid Python syntax: {e}")
    
    def _get_current_scope(self):
        """Get the current scope path as a string."""
        return ".".join(self.scope_stack) if self.scope_stack else "global"
    
    def _add_symbol(self, name, symbol_type, owner=None):
        """Add a symbol to the symbol table."""
        scope = self._get_current_scope()
        full_name = f"{scope}.{name}" if scope != "global" else name
        self.symbol_table[full_name] = {
            'type': symbol_type,
            'owner': owner,
            'scope': scope
        }
    
    def _lookup_symbol(self, name):
        """Look up a symbol in the symbol table, checking current scope first."""
        # Try current scope first
        current_scope = self._get_current_scope()
        full_name = f"{current_scope}.{name}" if current_scope != "global" else name
        
        if full_name in self.symbol_table:
            return self.symbol_table[full_name]
        
        # Try parent scopes
        scope_parts = self.scope_stack[:]
        while scope_parts:
            scope_parts.pop()
            scope = ".".join(scope_parts) if scope_parts else "global"
            test_name = f"{scope}.{name}" if scope != "global" else name
            if test_name in self.symbol_table:
                return self.symbol_table[test_name]
        
        return None
    
    def _visit_node(self, node):
        """Visit an AST node and convert it to tuple tree format."""
        if isinstance(node, ast.Module):
            children = []
            for child in node.body:
                result = self._visit_node(child)
                if result:
                    children.append(result)
            return ("module", "module", tuple(children) if children else None)
        
        elif isinstance(node, ast.ClassDef):
            # Add class to symbol table
            self._add_symbol(node.name, "class")
            
            # Enter class scope
            self.scope_stack.append(node.name)
            
            children = []
            
            # Add base classes
            for base in node.bases:
                base_result = self._visit_node(base)
                if base_result:
                    children.append(base_result)
            
            # Add decorators
            for decorator in node.decorator_list:
                dec_result = self._visit_node(decorator)
                if dec_result:
                    children.append(dec_result)
            
            # Add class body
            for child in node.body:
                result = self._visit_node(child)
                if result:
                    children.append(result)
            
            # Exit class scope
            self.scope_stack.pop()
            
            return (node.name, "class", tuple(children) if children else None)
        
        elif isinstance(node, ast.FunctionDef):
            # Add function to symbol table
            self._add_symbol(node.name, "function")
            
            # Enter function scope
            self.scope_stack.append(node.name)
            
            children = []
            
            # Add decorators
            for decorator in node.decorator_list:
                dec_result = self._visit_node(decorator)
                if dec_result:
                    children.append(dec_result)
            
            # Add parameters and track them
            for arg in node.args.args:
                if hasattr(arg, 'arg'):  # Python 3
                    param_name = arg.arg
                else:  # Python 2
                    param_name = arg.id
                self._add_symbol(param_name, "param")
                children.append((param_name, "param", None))
            
            # Add function body
            for child in node.body:
                result = self._visit_node(child)
                if result:
                    children.append(result)
            
            # Exit function scope
            self.scope_stack.pop()
            
            return (node.name, "function", tuple(children) if children else None)
        
        elif isinstance(node, ast.Assign):
            # Track variable assignments
            children = []
            
            # Handle the value being assigned
            value_result = self._visit_node(node.value)
            if value_result:
                children.append(value_result)
            
            # Handle targets (variables being assigned to)
            for target in node.targets:
                if isinstance(target, ast.Name):
                    # Determine the type of assignment
                    assigned_type = "variable"
                    owner_class = None
                    
                    if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
                        # This might be a class instantiation
                        class_name = node.value.func.id
                        symbol_info = self._lookup_symbol(class_name)
                        if symbol_info and symbol_info['type'] == 'class':
                            assigned_type = "instance"
                            owner_class = class_name
                    
                    self._add_symbol(target.id, assigned_type, owner_class)
                    children.append((target.id, assigned_type, (owner_class, None, None) if owner_class else None))
            
            return ("assignment", "assignment", tuple(children) if children else None)
        
        elif isinstance(node, ast.Call):
            children = []
            
            # Handle function calls, including method calls
            if isinstance(node.func, ast.Attribute):
                # This is a method call like obj.method() or os.path.join()
                obj_result = self._visit_node(node.func.value)
                method_name = node.func.attr
                
                # Try to determine the owner class/module
                if isinstance(node.func.value, ast.Name):
                    var_name = node.func.value.id
                    symbol_info = self._lookup_symbol(var_name)
                    if symbol_info and symbol_info.get('owner'):
                        owner_class = symbol_info['owner']
                        children.append((owner_class, "class_ref", None))
                    elif obj_result:
                        children.append(obj_result)
                elif isinstance(node.func.value, ast.Attribute):
                    # Handle chained attributes like os.path.join
                    if obj_result:
                        children.append(obj_result)
                
                # Process all arguments
                for arg in node.args:
                    arg_result = self._visit_node(arg)
                    if arg_result:
                        children.append(arg_result)
                
                # Process keyword arguments
                for keyword in node.keywords:
                    kw_result = self._visit_node(keyword.value)
                    if kw_result:
                        children.append((keyword.arg, "keyword", (kw_result,)))
                
                return (method_name, "method_call", tuple(children) if children else None)
            
            elif isinstance(node.func, ast.Name):
                # Regular function call
                func_name = node.func.id
                symbol_info = self._lookup_symbol(func_name)
                
                # Process all arguments
                for arg in node.args:
                    arg_result = self._visit_node(arg)
                    if arg_result:
                        children.append(arg_result)
                
                # Process keyword arguments
                for keyword in node.keywords:
                    kw_result = self._visit_node(keyword.value)
                    if kw_result:
                        children.append((keyword.arg, "keyword", (kw_result,)))
                
                if symbol_info and symbol_info['type'] == 'class':
                    # This is a class instantiation
                    return (func_name, "class_instantiation", tuple(children) if children else None)
                else:
                    return (func_name, "function_call", tuple(children) if children else None)
            
            else:
                # Handle other types of callable expressions
                func_result = self._visit_node(node.func)
                if func_result:
                    children.append(func_result)
                
                # Process all arguments
                for arg in node.args:
                    arg_result = self._visit_node(arg)
                    if arg_result:
                        children.append(arg_result)
                
                # Process keyword arguments
                for keyword in node.keywords:
                    kw_result = self._visit_node(keyword.value)
                    if kw_result:
                        children.append((keyword.arg, "keyword", (kw_result,)))
                
                return ("call", "function_call", tuple(children) if children else None)
        
        elif isinstance(node, ast.Name):
            # Check if this name refers to a known symbol
            symbol_info = self._lookup_symbol(node.id)
            if symbol_info:
                if symbol_info.get('owner'):
                    return (node.id, symbol_info['type'], (symbol_info['owner'], "class_ref", None))
                else:
                    return (node.id, symbol_info['type'], None)
            return (node.id, None, None)
        
        elif isinstance(node, ast.Attribute):
            # Handle attribute access like os.path
            value_result = self._visit_node(node.value)
            if value_result:
                return (node.attr, "attribute", (value_result,))
            return (node.attr, "attribute", None)
        
        elif isinstance(node, ast.Str):
            # String literal
            return (repr(node.s), "string", None)
        
        elif isinstance(node, ast.Num):
            # Number literal
            return (str(node.n), "number", None)
        
        elif isinstance(node, ast.Constant):  # Python 3.8+
            # Constant literal (string, number, etc.)
            return (repr(node.value), "constant", None)
        
        elif isinstance(node, ast.Expr):
            return self._visit_node(node.value)
        
        # Handle Python 2 print statement (only if running on Python 2)
        elif hasattr(ast, 'Print') and isinstance(node, ast.Print):
            children = []
            if node.values:
                for value in node.values:
                    value_result = self._visit_node(value)
                    if value_result:
                        children.append(value_result)
            return ("print", "function_call", tuple(children) if children else None)
        
        elif isinstance(node, (ast.If, ast.For, ast.While, ast.With)):
            # For control structures, recursively parse their bodies
            children = []
            if hasattr(node, 'body'):
                for child in node.body:
                    result = self._visit_node(child)
                    if result:
                        children.append(result)
            return (type(node).__name__.lower(), "control", tuple(children) if children else None)
        
        else:
            return None

def parse_python_code(code):
    """Convenience function to parse Python code."""
    parser = PythonParser()
    return parser.parse(code)

# Example usage
if __name__ == "__main__":
    code = '''
class A(object):
   @test
   def fn(self, a, b, c):
      print(a, b, c)

class B(object):
   def fn(self):
      a = A()
      a.fn(1, 2, os.path.join("a", "b"))
'''
    
    parser = PythonParser()
    result = parser.parse(code)
    print(result)
    
    # Test with more complex code
    complex_code = '''
class MyClass(BaseClass):
    @property
    @decorator
    def method(self, x, y):
        if x > 0:
            print("positive")
        return x + y
    
    def another_method(self):
        pass
'''
    
    result2 = parser.parse(complex_code)
    print("\nComplex example:")
    print(result2)
