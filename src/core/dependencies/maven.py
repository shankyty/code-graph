import os
import xml.etree.ElementTree as ET
from functools import lru_cache
from src.core.interfaces import DependencyResolver, Dependency
from typing import List, Optional

class MavenResolver(DependencyResolver):
    def resolve(self, file_path: str) -> List[Dependency]:
        pom_path = self._find_pom_from_dir(os.path.dirname(os.path.abspath(file_path)))
        if not pom_path:
            return []
        # Return a copy to avoid side effects on cached list
        return list(self._parse_pom(pom_path))

    @lru_cache(maxsize=None)
    def _find_pom_from_dir(self, current_dir: str) -> Optional[str]:
        # Traverse up to root
        while True:
            pom = os.path.join(current_dir, "pom.xml")
            if os.path.exists(pom):
                return pom
            parent = os.path.dirname(current_dir)
            if parent == current_dir:
                break
            current_dir = parent
        return None

    @lru_cache(maxsize=None)
    def _parse_pom(self, pom_path: str) -> List[Dependency]:
        deps = []
        try:
            tree = ET.parse(pom_path)
            root = tree.getroot()

            # Handle namespaces
            ns = {}
            if root.tag.startswith("{"):
                uri = root.tag.split("}")[0].strip("{")
                ns = {"mvn": uri}

            if ns:
                # Find all dependencies under <dependencies>
                dependencies_node = root.find("mvn:dependencies", ns)
                if dependencies_node is not None:
                    dependency_nodes = dependencies_node.findall("mvn:dependency", ns)
                else:
                    dependency_nodes = []
            else:
                dependencies_node = root.find("dependencies")
                if dependencies_node is not None:
                    dependency_nodes = dependencies_node.findall("dependency")
                else:
                    dependency_nodes = []

            for dep in dependency_nodes:
                group_id_node = dep.find("mvn:groupId", ns) if ns else dep.find("groupId")
                artifact_id_node = dep.find("mvn:artifactId", ns) if ns else dep.find("artifactId")
                version_node = dep.find("mvn:version", ns) if ns else dep.find("version")

                group_id = group_id_node.text if group_id_node is not None else ""
                artifact_id = artifact_id_node.text if artifact_id_node is not None else ""
                version = version_node.text if version_node is not None else None

                full_name = f"{group_id}:{artifact_id}"
                deps.append(Dependency(name=full_name, version=version, type="maven"))
        except Exception as e:
            # We don't want to crash the whole process if one POM is bad
            print(f"Error parsing POM {pom_path}: {e}")

        return deps
