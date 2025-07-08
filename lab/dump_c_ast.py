import clang.cindex
from clang.cindex import Index, CursorKind, TypeKind

class ASTDumper:
    def __init__(self):
        self.indent_level = 0
    
    def dump_node(self, node):
        """Dump a single AST node with detailed information"""
        indent = "  " * self.indent_level
        
        # Basic node info
        print(f"{indent}{node.kind.name}")
        print(f"{indent}  Spelling: '{node.spelling}'")
        print(f"{indent}  Display name: '{node.displayname}'")
        
        # Location info
        if node.location.file:
            print(f"{indent}  Location: {node.location.file.name}:{node.location.line}:{node.location.column}")
        
        # Type information
        if node.type.kind != TypeKind.INVALID:
            print(f"{indent}  Type: {node.type.spelling}")
        
        # Function-specific info
        if node.kind == CursorKind.FUNCTION_DECL:
            print(f"{indent}  Return type: {node.result_type.spelling}")
            #print(f"{indent}  Arguments: {node.get_num_arguments()}")
            print(f"{indent}  Arguments: {len(list(node.get_arguments()))}")
            for i, arg in enumerate(node.get_arguments()):
                print(f"{indent}    Arg {i}: {arg.spelling} ({arg.type.spelling})")
        
        # Variable-specific info
        elif node.kind == CursorKind.VAR_DECL:
            print(f"{indent}  Storage class: {node.storage_class}")
        
        # Class/struct info
        elif node.kind in [CursorKind.CLASS_DECL, CursorKind.STRUCT_DECL]:
            print(f"{indent}  Is definition: {node.is_definition()}")
        
        print()  # Empty line for readability
    
    def dump_ast(self, node):
        """Recursively dump the entire AST"""
        self.dump_node(node)
        
        self.indent_level += 1
        for child in node.get_children():
            self.dump_ast(child)
        self.indent_level -= 1

def parse_and_dump(code, filename, include_paths=None, compiler_args=None):
    """Parse file and dump AST with custom options"""
    if include_paths is None:
        include_paths = []
    if compiler_args is None:
        compiler_args = ['-std=c++17']
    
    # Add include paths to compiler args
    for path in include_paths:
        compiler_args.extend(['-I', path])
    
    index = Index.create()
    tu = index.parse(filename, args=compiler_args, unsaved_files=[(filename, code)])
    
    # Report diagnostics
    for diag in tu.diagnostics:
        severity = ["Ignored", "Note", "Warning", "Error", "Fatal"][diag.severity]
        print(f"{severity}: {diag}")
    
    # Dump AST
    dumper = ASTDumper()
    dumper.dump_ast(tu.cursor)

# Usage example
if __name__ == "__main__":
    parse_and_dump("""
#include <stdio.h>

int main() {
   printf("hello world");
   return 0;
}
""", "example.cpp", 
                   include_paths=["/usr/include", "/usr/local/include"],
                   compiler_args=["-std=c++17", "-Wall"])
