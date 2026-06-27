import { Plugin, Notice, TFile, TFolder, Vault } from "obsidian";
import { UnixSocketClient } from "./ipc/client";
import { NoteData } from "./types/messages";

const DEFAULT_SETTINGS = {
  wsPort: 18749,
  vaultPath: "",
  autoSync: true,
  syncInterval: 5000,
};

interface AkatsukiSettings {
  wsPort: number;
  vaultPath: string;
  autoSync: boolean;
  syncInterval: number;
}

export default class AkatsukiPlugin extends Plugin {
  settings: AkatsukiSettings = DEFAULT_SETTINGS;
  client: UnixSocketClient | null = null;
  syncTimer: number | null = null;
  statusBarEl: HTMLElement | null = null;

  async onload() {
    await this.loadSettings();
    this.addSettingTab(new AkatsukiSettingTab(this.app, this));

    this.statusBarEl = this.addStatusBarItem();
    this.statusBarEl.setText("AKATSUKI: disconnected");

    this.addCommand({
      id: "akatsuki-sync-now",
      name: "Sync now with Hermes",
      callback: () => this.syncNow(),
    });

    this.addCommand({
      id: "akatsuki-push-note",
      name: "Push current note to Hermes",
      callback: () => this.pushCurrentNote(),
    });

    this.addCommand({
      id: "akatsuki-connect",
      name: "Connect to Hermes bridge",
      callback: () => this.connect(),
    });

    this.addCommand({
      id: "akatsuki-disconnect",
      name: "Disconnect from Hermes bridge",
      callback: () => this.disconnect(),
    });

    this.registerEvent(
      this.app.vault.on("modify", (file) => this.onFileChange(file))
    );

    if (this.settings.autoSync) {
      this.connect();
    }
  }

  async onunload() {
    this.disconnect();
  }

  async connect() {
    if (this.client) return;
    this.client = new UnixSocketClient(this.settings.wsPort);
    try {
      await this.client.connect();
      this.updateStatus("connected");
      new Notice("AKATSUKI: connected to Hermes");

      this.client.on("note/changed", (evt) => {
        const payload = evt.params.payload as { path: string; action: string };
        new Notice(`Hermes ${payload.action}: ${payload.path}`);
        if (payload.action === "write" || payload.action === "delete") {
          this.refreshFile(payload.path);
        }
      });

      if (this.settings.autoSync && this.settings.syncInterval > 0) {
        this.syncTimer = window.setInterval(
          () => this.syncNow(),
          this.settings.syncInterval
        );
      }
    } catch (e) {
      this.updateStatus("connection failed");
      new Notice(`AKATSUKI: connection failed - ${e.message}`);
      this.client = null;
    }
  }

  disconnect() {
    if (this.syncTimer) {
      clearInterval(this.syncTimer);
      this.syncTimer = null;
    }
    if (this.client) {
      this.client.disconnect();
      this.client = null;
    }
    this.updateStatus("disconnected");
  }

  updateStatus(state: string) {
    if (this.statusBarEl) {
      this.statusBarEl.setText(`AKATSUKI: ${state}`);
    }
  }

  async syncNow() {
    if (!this.client) {
      await this.connect();
      if (!this.client) return;
    }
    try {
      const notes = this.app.vault.getMarkdownFiles();
      for (const file of notes) {
        const content = await this.app.vault.read(file);
        const noteData = this.buildNoteData(file, content);
        await this.client.call("note/write", { note: noteData });
      }
      new Notice(`AKATSUKI: synced ${notes.length} notes`);
    } catch (e) {
      new Notice(`AKATSUKI: sync failed - ${e.message}`);
    }
  }

  async pushCurrentNote() {
    if (!this.client) {
      await this.connect();
      if (!this.client) return;
    }
    const file = this.app.workspace.getActiveFile();
    if (!file) {
      new Notice("No active file");
      return;
    }
    try {
      const content = await this.app.vault.read(file);
      const noteData = this.buildNoteData(file, content);
      await this.client.call("note/write", { note: noteData });
      new Notice(`Pushed: ${file.path}`);
    } catch (e) {
      new Notice(`Push failed: ${e.message}`);
    }
  }

  async onFileChange(file: TFile) {
    if (!this.client || !this.settings.autoSync) return;
    if (file.extension !== "md") return;
    try {
      const content = await this.app.vault.read(file);
      const noteData = this.buildNoteData(file, content);
      await this.client.call("note/write", { note: noteData });
    } catch {
      // silent
    }
  }

  buildNoteData(file: TFile, content: string): NoteData {
    const fm = this.parseFrontmatter(content);
    return {
      id: file.path,
      path: file.path,
      title: file.basename,
      content: this.stripFrontmatter(content),
      tags: fm.tags || [],
      links: [],
      frontmatter: fm,
      checksum: "",
      version: 0,
      created: file.stat.ctime,
      modified: file.stat.mtime,
      source: "obsidian",
    };
  }

  parseFrontmatter(content: string): Record<string, unknown> {
    const match = content.match(/^---\n([\s\S]*?)\n---/);
    if (!match) return {};
    const result: Record<string, unknown> = {};
    for (const line of match[1].split("\n")) {
      const sep = line.indexOf(":");
      if (sep > 0) {
        const key = line.slice(0, sep).trim();
        let val: unknown = line.slice(sep + 1).trim();
        if (typeof val === "string" && val.startsWith("[")) {
          try { val = JSON.parse(val); } catch { /* keep string */ }
        }
        result[key] = val;
      }
    }
    return result;
  }

  stripFrontmatter(content: string): string {
    return content.replace(/^---\n[\s\S]*?\n---\n*/, "").trim();
  }

  async refreshFile(path: string) {
    const file = this.app.vault.getAbstractFileByPath(path);
    if (file instanceof TFile) {
      this.app.workspace.trigger("akatsuki:refresh", file);
    }
  }

  async loadSettings() {
    const data = await this.loadData();
    this.settings = { ...DEFAULT_SETTINGS, ...data };
  }

  async saveSettings() {
    await this.saveData(this.settings);
  }
}

import { App, PluginSettingTab, Setting } from "obsidian";

class AkatsukiSettingTab extends PluginSettingTab {
  plugin: AkatsukiPlugin;

  constructor(app: App, plugin: AkatsukiPlugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display(): void {
    const { containerEl } = this;
    containerEl.empty();
    containerEl.createEl("h2", { text: "AKATSUKI Settings" });

    new Setting(containerEl)
      .setName("WebSocket port")
      .setDesc("Port for Hermes bridge connection")
      .addText((text) =>
        text
          .setPlaceholder("18749")
          .setValue(String(this.plugin.settings.wsPort))
          .onChange(async (v) => {
            this.plugin.settings.wsPort = parseInt(v) || 18749;
            await this.plugin.saveSettings();
          })
      );

    new Setting(containerEl)
      .setName("Auto-sync")
      .setDesc("Automatically sync notes with Hermes")
      .addToggle((toggle) =>
        toggle
          .setValue(this.plugin.settings.autoSync)
          .onChange(async (v) => {
            this.plugin.settings.autoSync = v;
            await this.plugin.saveSettings();
            if (v) this.plugin.connect();
            else this.plugin.disconnect();
          })
      );

    new Setting(containerEl)
      .setName("Sync interval (ms)")
      .setDesc("How often to auto-sync")
      .addText((text) =>
        text
          .setPlaceholder("5000")
          .setValue(String(this.plugin.settings.syncInterval))
          .onChange(async (v) => {
            this.plugin.settings.syncInterval = parseInt(v) || 5000;
            await this.plugin.saveSettings();
          })
      );

    new Setting(containerEl).addButton((btn) =>
      btn.setButtonText("Test Connection").onClick(async () => {
        try {
          const client = new UnixSocketClient(this.plugin.settings.wsPort);
          await client.connect();
          const result = await client.call("ping", {});
          client.disconnect();
          new Notice(
            "AKATSUKI: connection OK - " + JSON.stringify(result)
          );
        } catch (e) {
          new Notice("AKATSUKI: connection failed - " + e.message);
        }
      })
    );
  }
}
