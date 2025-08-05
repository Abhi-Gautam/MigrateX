"""Metadata management for code transformation tracking."""

import uuid
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from pydantic import BaseModel


class FunctionMetadata(BaseModel):
    """Metadata model for a single function transformation."""
    id: str
    source_function: Dict
    test_info: Optional[Dict] = None
    status: str = "extracted"
    created_at: datetime
    updated_at: datetime
    dependencies: List[str] = []
    translation_info: Optional[Dict] = None


class MetadataManager:
    """Manages metadata for function extraction and test association."""
    
    def __init__(self):
        self.metadata_store: Dict[str, FunctionMetadata] = {}
        self.function_name_index: Dict[str, str] = {}  # function_name -> metadata_id
    
    def create_function_metadata(self, function_info: Dict) -> str:
        """Create a new metadata entry for an extracted function."""
        metadata_id = str(uuid.uuid4())
        now = datetime.now()
        
        metadata = FunctionMetadata(
            id=metadata_id,
            source_function=function_info,
            status="extracted",
            created_at=now,
            updated_at=now,
            dependencies=function_info.get("dependencies", [])
        )
        
        self.metadata_store[metadata_id] = metadata
        self.function_name_index[function_info["name"]] = metadata_id
        
        return metadata_id
    
    def get_metadata(self, metadata_id: str) -> Optional[Dict]:
        """Retrieve metadata by ID."""
        if metadata_id in self.metadata_store:
            return self.metadata_store[metadata_id].model_dump()
        return None
    
    def get_metadata_by_function_name(self, function_name: str) -> Optional[Dict]:
        """Retrieve metadata by function name."""
        if function_name in self.function_name_index:
            metadata_id = self.function_name_index[function_name]
            return self.get_metadata(metadata_id)
        return None
    
    def associate_existing_test(self, metadata_id: str, test_info: Dict) -> bool:
        """Associate an existing test with a function's metadata."""
        if metadata_id not in self.metadata_store:
            return False
        
        metadata = self.metadata_store[metadata_id]
        metadata.test_info = {
            "test_name": test_info["name"],
            "test_content": test_info["content"],
            "test_file": test_info["file"],
            "test_type": "existing",
            "language": test_info["language"]
        }
        metadata.status = "test_associated"
        metadata.updated_at = datetime.now()
        
        return True
    
    def associate_generated_test(self, metadata_id: str, test_info: Dict) -> bool:
        """Associate a generated test with a function's metadata."""
        if metadata_id not in self.metadata_store:
            return False
        
        metadata = self.metadata_store[metadata_id]
        metadata.test_info = {
            "test_name": test_info["test_name"],
            "test_content": test_info["test_content"],
            "test_type": "generated",
            "language": test_info["language"],
            "source_function": test_info.get("source_function", metadata.source_function["name"])
        }
        metadata.status = "test_generated"
        metadata.updated_at = datetime.now()
        
        return True
    
    def update_status(self, metadata_id: str, new_status: str) -> bool:
        """Update the status of a metadata entry."""
        if metadata_id not in self.metadata_store:
            return False
        
        metadata = self.metadata_store[metadata_id]
        metadata.status = new_status
        metadata.updated_at = datetime.now()
        
        return True
    
    def get_all_metadata(self) -> List[Dict]:
        """Get all metadata entries."""
        return [metadata.model_dump() for metadata in self.metadata_store.values()]
    
    def get_metadata_by_status(self, status: str) -> List[Dict]:
        """Get metadata entries by status."""
        return [
            metadata.model_dump() 
            for metadata in self.metadata_store.values() 
            if metadata.status == status
        ]
    
    def delete_metadata(self, metadata_id: str) -> bool:
        """Delete a metadata entry."""
        if metadata_id not in self.metadata_store:
            return False
        
        metadata = self.metadata_store[metadata_id]
        function_name = metadata.source_function["name"]
        
        del self.metadata_store[metadata_id]
        if function_name in self.function_name_index:
            del self.function_name_index[function_name]
        
        return True