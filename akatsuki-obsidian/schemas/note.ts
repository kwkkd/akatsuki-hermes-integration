export interface Note {
  id: string;                  // UUID v4
  path: string;                // Vault-relative path (e.g., "AKATSUKI/Missions/OP-001.md")
  title: string;
  content: string;
  tags: string[];
  links: string[];             // [[wikilinks]] extracted
  frontmatter: Record<string, unknown>;
  checksum: string;            // SHA-256 of content
  version: number;
  created: number;             // Unix ms
  modified: number;            // Unix ms
  source: "hermes" | "obsidian" | "user";
}

export interface NoteDelta {
  id: string;
  path?: string;
  title?: string;
  content?: string;
  tags?: string[];
  frontmatter?: Record<string, unknown>;
  checksum?: string;
  version: number;
  baseVersion: number;         // version we branched from
  operations: CrdtOperation[];
}

export interface NoteRef {
  id: string;
  path: string;
  title: string;
  tags: string[];
  modified: number;
  checksum: string;
}

export interface Folder {
  path: string;
  notes: NoteRef[];
  folders: Folder[];
  modified: number;
}
