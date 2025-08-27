import os
import json
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re


class XMPWriter:
    def __init__(self):
        # Register namespaces
        self.namespaces = {
            'x': 'adobe:ns:meta/',
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
            'xmp': 'http://ns.adobe.com/xap/1.0/',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'xmpMM': 'http://ns.adobe.com/xap/1.0/mm/',
            'stRef': 'http://ns.adobe.com/xap/1.0/sType/ResourceRef#',
            'iptc': 'http://iptc.org/std/Iptc4xmpCore/1.0/xmlns/',
            'slx': 'http://solvx.uk/ns/slx/1.0/'
        }
        
        # Register with ElementTree
        for prefix, uri in self.namespaces.items():
            ET.register_namespace(prefix, uri)
    
    def normalize_field_name(self, field: str) -> str:
        """Convert field name to lowerCamelCase."""
        # Remove non-alphanumeric, collapse whitespace/underscores
        field = re.sub(r'[^a-zA-Z0-9\s_]', '', field)
        field = re.sub(r'[\s_]+', ' ', field).strip()
        
        # Convert to lowerCamelCase
        parts = field.split()
        if not parts:
            return 'field'
        
        result = parts[0].lower()
        for part in parts[1:]:
            result += part.capitalize()
        
        return result
    
    def create_field_mapping(self, fields: List[str]) -> Dict[str, str]:
        """Create mapping from original to normalized field names."""
        mapping = {}
        for field in fields:
            mapping[field] = self.normalize_field_name(field)
        return mapping
    
    def write_xmp_sidecar(self, image_path: Path, row: Dict[str, str], 
                         selected_fields: List[str], overlay_spec: str,
                         join_key: str, csv_path: Path, 
                         hashes: Dict[str, str], field_order: List[str] = None,
                         overlay_positions: Dict[str, Tuple[float, float]] = None) -> Path:
        """Write XMP sidecar file with metadata."""
        
        # Create field mapping
        field_mapping = self.create_field_mapping(selected_fields)
        
        # Build XMP structure
        xmp_root = self._create_xmp_root()
        rdf_elem = self._create_rdf_element(xmp_root)
        desc_elem = self._create_description_element(rdf_elem)
        
        # Add standard XMP fields
        self._add_standard_fields(desc_elem, image_path, hashes)
        
        # Add CSV-derived fields
        self._add_csv_fields(desc_elem, row, selected_fields, field_mapping)
        
        # Add custom metadata
        self._add_custom_metadata(desc_elem, csv_path, hashes, join_key, 
                                 selected_fields, field_mapping, overlay_spec,
                                 field_order, overlay_positions)
        
        # Write to temp file first (atomic write)
        xmp_path = image_path.with_suffix('.xmp')
        temp_path = xmp_path.with_suffix('.xmp.tmp')
        
        # Format XML with proper header
        tree = ET.ElementTree(xmp_root)
        ET.indent(tree, space='  ')
        
        with open(temp_path, 'wb') as f:
            f.write(b"<?xml version='1.0' encoding='UTF-8'?>\n")
            f.write(b"<?xpacket begin='\\ufeff' id='W5M0MpCehiHzreSzNTczkc9d'?>\n")
            tree.write(f, encoding='UTF-8', xml_declaration=False)
            f.write(b"\n<?xpacket end='w'?>")
        
        # Atomic replace
        os.replace(temp_path, xmp_path)
        
        # Validate by re-parsing
        self._validate_xmp(xmp_path)
        
        return xmp_path
    
    def _create_xmp_root(self) -> ET.Element:
        """Create XMP root element."""
        return ET.Element('{adobe:ns:meta/}xmpmeta')
    
    def _create_rdf_element(self, parent: ET.Element) -> ET.Element:
        """Create RDF element."""
        rdf = ET.SubElement(parent, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF')
        return rdf
    
    def _create_description_element(self, parent: ET.Element) -> ET.Element:
        """Create Description element with namespace declarations."""
        desc = ET.SubElement(parent, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description')
        desc.set('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about', '')
        
        # Add namespace declarations
        for prefix, uri in self.namespaces.items():
            if prefix not in ['x', 'rdf']:  # These are on parent elements
                desc.set(f'xmlns:{prefix}', uri)
        
        return desc
    
    def _add_standard_fields(self, desc: ET.Element, image_path: Path, 
                            hashes: Dict[str, str]) -> None:
        """Add standard XMP fields."""
        # Creator tool and date
        ET.SubElement(desc, '{http://ns.adobe.com/xap/1.0/}CreatorTool').text = 'SlateLink 0.2.0'
        ET.SubElement(desc, '{http://ns.adobe.com/xap/1.0/}CreateDate').text = \
            datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # DerivedFrom structure
        derived = ET.SubElement(desc, '{http://ns.adobe.com/xap/1.0/mm/}DerivedFrom')
        ET.SubElement(derived, '{http://ns.adobe.com/xap/1.0/sType/ResourceRef#}filePath').text = \
            image_path.name
        ET.SubElement(derived, '{http://ns.adobe.com/xap/1.0/sType/ResourceRef#}documentID').text = \
            f"sha256:{hashes.get('jpeg', '')}"
        ET.SubElement(derived, '{http://ns.adobe.com/xap/1.0/sType/ResourceRef#}instanceID').text = \
            str(uuid.uuid4())
    
    def _add_csv_fields(self, desc: ET.Element, row: Dict[str, str], 
                       selected_fields: List[str], field_mapping: Dict[str, str]) -> None:
        """Add CSV-derived fields with special handling for standard fields."""
        for field in selected_fields:
            if field not in row:
                continue
            
            value = row[field]  # Preserve exactly as string
            normalized = field_mapping[field]
            
            # Check for standard field mappings
            if field.lower() in ['creator', 'byline']:
                # Add to IPTC
                ET.SubElement(desc, '{http://iptc.org/std/Iptc4xmpCore/1.0/xmlns/}Creator').text = value
                # Also mirror to custom namespace
                ET.SubElement(desc, f'{{http://solvx.uk/ns/slx/1.0/}}{normalized}').text = value
                
            elif field.lower() == 'copyright':
                # Add to Dublin Core
                rights = ET.SubElement(desc, '{http://purl.org/dc/elements/1.1/}rights')
                alt = ET.SubElement(rights, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Alt')
                li = ET.SubElement(alt, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}li')
                li.set('{http://www.w3.org/XML/1998/namespace}lang', 'x-default')
                li.text = value
                
            elif field.lower() in ['description', 'notes']:
                # Add to Dublin Core
                dc_desc = ET.SubElement(desc, '{http://purl.org/dc/elements/1.1/}description')
                alt = ET.SubElement(dc_desc, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Alt')
                li = ET.SubElement(alt, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}li')
                li.set('{http://www.w3.org/XML/1998/namespace}lang', 'x-default')
                li.text = value
                # Mirror to custom
                ET.SubElement(desc, f'{{http://solvx.uk/ns/slx/1.0/}}{normalized}').text = value
                
            elif field.lower() in ['title', 'slate']:
                # Add to Dublin Core
                title = ET.SubElement(desc, '{http://purl.org/dc/elements/1.1/}title')
                alt = ET.SubElement(title, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Alt')
                li = ET.SubElement(alt, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}li')
                li.set('{http://www.w3.org/XML/1998/namespace}lang', 'x-default')
                li.text = value
                
            else:
                # Add to custom namespace only
                ET.SubElement(desc, f'{{http://solvx.uk/ns/slx/1.0/}}{normalized}').text = value
    
    def _add_custom_metadata(self, desc: ET.Element, csv_path: Path, 
                            hashes: Dict[str, str], join_key: str,
                            selected_fields: List[str], field_mapping: Dict[str, str],
                            overlay_spec: str, field_order: List[str] = None,
                            overlay_positions: Dict[str, Tuple[float, float]] = None) -> None:
        """Add custom SlateLink metadata."""
        # CSV info
        ET.SubElement(desc, '{http://solvx.uk/ns/slx/1.0/}csvFileName').text = \
            csv_path.name if csv_path else ''
        ET.SubElement(desc, '{http://solvx.uk/ns/slx/1.0/}csvSHA256').text = \
            f"sha256:{hashes.get('csv', '')}"
        ET.SubElement(desc, '{http://solvx.uk/ns/slx/1.0/}jpegSHA256').text = \
            f"sha256:{hashes.get('jpeg', '')}"
        
        # Join key
        ET.SubElement(desc, '{http://solvx.uk/ns/slx/1.0/}joinKey').text = join_key
        
        # Field mapping
        ET.SubElement(desc, '{http://solvx.uk/ns/slx/1.0/}fieldMap').text = \
            json.dumps(field_mapping)
        
        # Selected fields as bag
        fields_elem = ET.SubElement(desc, '{http://solvx.uk/ns/slx/1.0/}selectedFields')
        bag = ET.SubElement(fields_elem, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Bag')
        for field in selected_fields:
            ET.SubElement(bag, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}li').text = field
        
        # Overlay spec
        ET.SubElement(desc, '{http://solvx.uk/ns/slx/1.0/}overlaySpec').text = overlay_spec
        
        # Back-compat guard: only write if user-defined field order exists
        if field_order:
            ET.SubElement(desc, '{http://solvx.uk/ns/slx/1.0/}fieldOrder').text = \
                json.dumps(field_order)
        
        # Back-compat guard: only write if user-defined positions exist
        if overlay_positions:
            # Normalize positions to 4 decimal places
            normalized_positions = {
                field: [round(pos[0], 4), round(pos[1], 4)] 
                for field, pos in overlay_positions.items()
            }
            ET.SubElement(desc, '{http://solvx.uk/ns/slx/1.0/}overlayPositions').text = \
                json.dumps(normalized_positions)
    
    def _validate_xmp(self, xmp_path: Path) -> None:
        """Validate XMP file by parsing it."""
        try:
            tree = ET.parse(xmp_path)
            # If parsing succeeds, the XML is well-formed
        except ET.ParseError as e:
            raise ValueError(f"Generated XMP is not well-formed: {e}")