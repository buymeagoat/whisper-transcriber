"""
T036: Real-time Collaboration Features - Operational Transform Engine
Implements operational transform for conflict-free collaborative editing.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, asdict

from ..utils.logger import get_logger

logger = get_logger("operational_transform")


class OperationType(Enum):
    """Types of text operations for collaborative editing."""
    INSERT = "insert"
    DELETE = "delete"
    RETAIN = "retain"
    FORMAT = "format"


@dataclass
class TextOperation:
    """Represents a single text operation."""
    type: OperationType
    position: int
    content: Optional[str] = None
    length: Optional[int] = None
    attributes: Optional[Dict[str, Any]] = None
    user_id: Optional[int] = None
    timestamp: Optional[str] = None
    operation_id: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert operation to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TextOperation':
        """Create operation from dictionary."""
        return cls(
            type=OperationType(data['type']),
            position=data['position'],
            content=data.get('content'),
            length=data.get('length'),
            attributes=data.get('attributes'),
            user_id=data.get('user_id'),
            timestamp=data.get('timestamp'),
            operation_id=data.get('operation_id')
        )


class OperationalTransform:
    """
    Implements operational transform algorithm for collaborative text editing.
    Based on the Jupiter algorithm for consistency maintenance.
    """
    
    @staticmethod
    def transform_operations(op1: TextOperation, op2: TextOperation) -> Tuple[TextOperation, TextOperation]:
        """
        Transform two concurrent operations to maintain document consistency.
        
        Args:
            op1: First operation
            op2: Second operation
            
        Returns:
            Tuple of transformed operations (op1', op2')
        """
        # Create copies to avoid modifying originals
        op1_prime = TextOperation(
            type=op1.type,
            position=op1.position,
            content=op1.content,
            length=op1.length,
            attributes=op1.attributes,
            user_id=op1.user_id,
            timestamp=op1.timestamp,
            operation_id=op1.operation_id
        )
        
        op2_prime = TextOperation(
            type=op2.type,
            position=op2.position,
            content=op2.content,
            length=op2.length,
            attributes=op2.attributes,
            user_id=op2.user_id,
            timestamp=op2.timestamp,
            operation_id=op2.operation_id
        )
        
        # Transform based on operation types
        if op1.type == OperationType.INSERT and op2.type == OperationType.INSERT:
            op1_prime, op2_prime = OperationalTransform._transform_insert_insert(op1_prime, op2_prime)
        
        elif op1.type == OperationType.INSERT and op2.type == OperationType.DELETE:
            op1_prime, op2_prime = OperationalTransform._transform_insert_delete(op1_prime, op2_prime)
        
        elif op1.type == OperationType.DELETE and op2.type == OperationType.INSERT:
            op2_prime, op1_prime = OperationalTransform._transform_insert_delete(op2_prime, op1_prime)
        
        elif op1.type == OperationType.DELETE and op2.type == OperationType.DELETE:
            op1_prime, op2_prime = OperationalTransform._transform_delete_delete(op1_prime, op2_prime)
        
        elif op1.type == OperationType.RETAIN and op2.type == OperationType.RETAIN:
            # Retain operations don't conflict
            pass
        
        else:
            # Handle mixed retain operations with insert/delete
            if op1.type == OperationType.RETAIN:
                op1_prime, op2_prime = OperationalTransform._transform_retain_other(op1_prime, op2_prime)
            elif op2.type == OperationType.RETAIN:
                op2_prime, op1_prime = OperationalTransform._transform_retain_other(op2_prime, op1_prime)
        
        return op1_prime, op2_prime
    
    @staticmethod
    def _transform_insert_insert(op1: TextOperation, op2: TextOperation) -> Tuple[TextOperation, TextOperation]:
        """Transform two concurrent insert operations."""
        if op1.position <= op2.position:
            # op1 comes before op2, adjust op2's position
            op2.position += len(op1.content or "")
        else:
            # op2 comes before op1, adjust op1's position
            op1.position += len(op2.content or "")
        
        return op1, op2
    
    @staticmethod
    def _transform_insert_delete(op_insert: TextOperation, op_delete: TextOperation) -> Tuple[TextOperation, TextOperation]:
        """Transform insert and delete operations."""
        delete_end = op_delete.position + (op_delete.length or 0)
        
        if op_insert.position <= op_delete.position:
            # Insert comes before delete range, adjust delete position
            op_delete.position += len(op_insert.content or "")
        elif op_insert.position >= delete_end:
            # Insert comes after delete range, adjust insert position
            op_insert.position -= (op_delete.length or 0)
        else:
            # Insert is within delete range, adjust insert position
            op_insert.position = op_delete.position
        
        return op_insert, op_delete
    
    @staticmethod
    def _transform_delete_delete(op1: TextOperation, op2: TextOperation) -> Tuple[TextOperation, TextOperation]:
        """Transform two concurrent delete operations."""
        op1_end = op1.position + (op1.length or 0)
        op2_end = op2.position + (op2.length or 0)
        
        if op1_end <= op2.position:
            # op1 comes completely before op2
            op2.position -= (op1.length or 0)
        elif op2_end <= op1.position:
            # op2 comes completely before op1
            op1.position -= (op2.length or 0)
        else:
            # Operations overlap, need to adjust both
            if op1.position < op2.position:
                if op1_end <= op2_end:
                    # op1 starts before op2 and ends within or at the same point
                    overlap = op1_end - op2.position
                    op1.length = op2.position - op1.position
                    op2.position = op1.position
                    op2.length = (op2.length or 0) - overlap
                else:
                    # op1 completely contains op2
                    op1.length = (op1.length or 0) - (op2.length or 0)
                    op2.length = 0  # op2 becomes no-op
            else:
                if op2_end <= op1_end:
                    # op2 starts before op1 and ends within or at the same point
                    overlap = op2_end - op1.position
                    op2.length = op1.position - op2.position
                    op1.position = op2.position
                    op1.length = (op1.length or 0) - overlap
                else:
                    # op2 completely contains op1
                    op2.length = (op2.length or 0) - (op1.length or 0)
                    op1.length = 0  # op1 becomes no-op
        
        return op1, op2
    
    @staticmethod
    def _transform_retain_other(op_retain: TextOperation, op_other: TextOperation) -> Tuple[TextOperation, TextOperation]:
        """Transform retain operation with another operation."""
        # Retain operations typically don't affect positioning
        # This is a simplified implementation
        return op_retain, op_other
    
    @staticmethod
    def apply_operation(text: str, operation: TextOperation) -> str:
        """
        Apply an operation to a text string.
        
        Args:
            text: Original text
            operation: Operation to apply
            
        Returns:
            Modified text
        """
        try:
            if operation.type == OperationType.INSERT:
                content = operation.content or ""
                position = max(0, min(operation.position, len(text)))
                return text[:position] + content + text[position:]
            
            elif operation.type == OperationType.DELETE:
                start = max(0, min(operation.position, len(text)))
                length = operation.length or 0
                end = min(start + length, len(text))
                return text[:start] + text[end:]
            
            elif operation.type == OperationType.RETAIN:
                # Retain operations don't modify the text
                return text
            
            elif operation.type == OperationType.FORMAT:
                # Format operations don't modify the text content
                # They would be handled by the formatting system
                return text
            
            else:
                logger.warning(f"Unknown operation type: {operation.type}")
                return text
        
        except Exception as e:
            logger.error(f"Error applying operation {operation.type}: {e}")
            return text
    
    @staticmethod
    def compose_operations(op1: TextOperation, op2: TextOperation) -> Optional[TextOperation]:
        """
        Compose two sequential operations into a single operation.
        
        Args:
            op1: First operation
            op2: Second operation
            
        Returns:
            Composed operation or None if composition is not possible
        """
        try:
            # Simple composition for same-type operations at same position
            if (op1.type == op2.type == OperationType.INSERT and 
                op1.position + len(op1.content or "") == op2.position):
                
                return TextOperation(
                    type=OperationType.INSERT,
                    position=op1.position,
                    content=(op1.content or "") + (op2.content or ""),
                    user_id=op1.user_id,
                    timestamp=op2.timestamp
                )
            
            elif (op1.type == op2.type == OperationType.DELETE and 
                  op1.position == op2.position):
                
                return TextOperation(
                    type=OperationType.DELETE,
                    position=op1.position,
                    length=(op1.length or 0) + (op2.length or 0),
                    user_id=op1.user_id,
                    timestamp=op2.timestamp
                )
            
            # More complex compositions would be handled here
            return None
        
        except Exception as e:
            logger.error(f"Error composing operations: {e}")
            return None


class DocumentState:
    """Manages the state of a collaborative document."""
    
    def __init__(self, initial_content: str = "", document_id: str = ""):
        self.document_id = document_id
        self.content = initial_content
        self.version = 0
        self.operation_history: List[TextOperation] = []
        self.pending_operations: Dict[int, List[TextOperation]] = {}
    
    def apply_operation(self, operation: TextOperation, user_id: int) -> bool:
        """
        Apply an operation to the document.
        
        Args:
            operation: Operation to apply
            user_id: ID of the user performing the operation
            
        Returns:
            True if operation was applied successfully
        """
        try:
            # Apply the operation
            new_content = OperationalTransform.apply_operation(self.content, operation)
            
            # Update document state
            self.content = new_content
            self.version += 1
            operation.user_id = user_id
            self.operation_history.append(operation)
            
            logger.info(f"Applied {operation.type.value} operation from user {user_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to apply operation: {e}")
            return False
    
    def transform_and_apply(self, operation: TextOperation, user_id: int, 
                          concurrent_operations: List[TextOperation]) -> TextOperation:
        """
        Transform an operation against concurrent operations and apply it.
        
        Args:
            operation: Operation to transform and apply
            user_id: ID of the user performing the operation
            concurrent_operations: List of concurrent operations to transform against
            
        Returns:
            Transformed operation
        """
        transformed_op = operation
        
        # Transform against all concurrent operations
        for concurrent_op in concurrent_operations:
            transformed_op, _ = OperationalTransform.transform_operations(
                transformed_op, concurrent_op
            )
        
        # Apply the transformed operation
        self.apply_operation(transformed_op, user_id)
        
        return transformed_op
    
    def get_operations_since_version(self, version: int) -> List[TextOperation]:
        """
        Get all operations since a specific version.
        
        Args:
            version: Version number to get operations since
            
        Returns:
            List of operations since the specified version
        """
        if version >= len(self.operation_history):
            return []
        
        return self.operation_history[version:]
    
    def get_document_info(self) -> dict:
        """Get current document information."""
        return {
            "document_id": self.document_id,
            "content": self.content,
            "version": self.version,
            "content_length": len(self.content),
            "operation_count": len(self.operation_history)
        }


class CollaborativeEditor:
    """High-level interface for collaborative editing operations."""
    
    def __init__(self):
        self.documents: Dict[str, DocumentState] = {}
    
    def create_document(self, document_id: str, initial_content: str = "") -> DocumentState:
        """Create a new collaborative document."""
        document = DocumentState(initial_content, document_id)
        self.documents[document_id] = document
        logger.info(f"Created collaborative document {document_id}")
        return document
    
    def get_document(self, document_id: str) -> Optional[DocumentState]:
        """Get a document by ID."""
        return self.documents.get(document_id)
    
    def apply_operation(self, document_id: str, operation: TextOperation, 
                       user_id: int) -> Optional[TextOperation]:
        """
        Apply an operation to a document with conflict resolution.
        
        Args:
            document_id: ID of the document
            operation: Operation to apply
            user_id: ID of the user performing the operation
            
        Returns:
            Transformed operation if successful, None otherwise
        """
        document = self.get_document(document_id)
        if not document:
            logger.error(f"Document {document_id} not found")
            return None
        
        try:
            # For simplicity, assume no concurrent operations for now
            # In a real implementation, you would get concurrent operations
            # from the collaboration manager
            concurrent_operations = []
            
            transformed_op = document.transform_and_apply(
                operation, user_id, concurrent_operations
            )
            
            return transformed_op
        
        except Exception as e:
            logger.error(f"Error applying operation to document {document_id}: {e}")
            return None
    
    def get_document_stats(self) -> dict:
        """Get statistics for all documents."""
        return {
            "total_documents": len(self.documents),
            "documents": {
                doc_id: doc.get_document_info()
                for doc_id, doc in self.documents.items()
            }
        }


# Global collaborative editor instance
collaborative_editor = CollaborativeEditor()