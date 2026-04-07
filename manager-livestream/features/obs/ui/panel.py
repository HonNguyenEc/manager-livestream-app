"""OBS UI panel with Config + Setting subtabs."""

from tkinter import ttk

from features.obs.domain.models import OBSConfig
from features.obs.ui.config_tab import OBSConfigTab
from features.obs.ui.playlist_tab import OBSPlaylistTab
from features.obs.ui.setting_tab import OBSSettingTab


class OBSPanel:
    """Composite OBS UI controls."""

    def __init__(
        self,
        parent,
        on_connect,
        on_disconnect,
        on_reload,
        on_load_config_file,
        on_load_scenes,
        on_load_sources,
        on_apply_scene,
        on_choose_folder,
        on_import_videos,
        on_start_queue,
        on_stop_queue,
        on_clear_queue,
        on_remove_video,
        on_move_up_video,
        on_move_down_video,
        on_skip_video,
        on_prioritize_video,
        on_set_video_cooldown,
    ):
        self.frame = ttk.Frame(parent, padding=10)

        notebook = ttk.Notebook(self.frame)
        notebook.pack(fill="both", expand=True)

        self.connection_tab = ttk.Frame(notebook, padding=10)
        self.setting_tab = ttk.Frame(notebook, padding=10)
        self.playlist_tab = ttk.Frame(notebook, padding=10)
        notebook.add(self.connection_tab, text="Connection")
        notebook.add(self.setting_tab, text="Scene & Sources")
        notebook.add(self.playlist_tab, text="Playlist")

        self.config_component = OBSConfigTab(self.connection_tab, on_connect, on_disconnect, on_reload, on_load_config_file)
        self.setting_component = OBSSettingTab(self.setting_tab, on_load_scenes, on_load_sources, on_apply_scene)
        self.playlist_component = OBSPlaylistTab(
            self.playlist_tab,
            on_choose_folder=on_choose_folder,
            on_import=on_import_videos,
            on_start=on_start_queue,
            on_stop=on_stop_queue,
            on_clear=on_clear_queue,
            on_remove=on_remove_video,
            on_move_up=on_move_up_video,
            on_move_down=on_move_down_video,
            on_skip=on_skip_video,
            on_prioritize=on_prioritize_video,
            on_set_cooldown=on_set_video_cooldown,
        )
        self.config_component.frame.pack(fill="both", expand=True)
        self.setting_component.frame.pack(fill="both", expand=True)
        self.playlist_component.frame.pack(fill="both", expand=True)

    def get_config(self) -> OBSConfig:
        return OBSConfig(
            host=self.config_component.host_var.get().strip(),
            port=self.config_component.port_var.get().strip(),
            password=self.config_component.password_var.get().strip(),
            scene_name=self.setting_component.scene_var.get().strip(),
            source_a_name=self.setting_component.source_a_var.get().strip(),
            source_b_name=self.setting_component.source_b_var.get().strip(),
            video_folder=self.playlist_component.folder_var.get().strip(),
            crossfade_seconds=self.setting_component.crossfade_var.get().strip(),
            default_cooldown_seconds=self.setting_component.default_cooldown_var.get().strip(),
        )

    def set_config(self, cfg: OBSConfig):
        self.config_component.host_var.set(cfg.host)
        self.config_component.port_var.set(str(cfg.port))
        self.config_component.password_var.set(cfg.password)
        self.setting_component.scene_var.set(cfg.scene_name)
        self.setting_component.source_a_var.set(cfg.source_a_name)
        self.setting_component.source_b_var.set(cfg.source_b_name)
        self.playlist_component.folder_var.set(cfg.video_folder)
        self.setting_component.crossfade_var.set(cfg.crossfade_seconds)
        self.setting_component.default_cooldown_var.set(cfg.default_cooldown_seconds)

    def set_status(self, text: str):
        self.config_component.status_var.set(text)

    def set_scenes(self, scenes: list[str]):
        self.setting_component.scene_combo["values"] = scenes
        if scenes and self.setting_component.scene_var.get() not in scenes:
            self.setting_component.scene_var.set(scenes[0])

    def set_sources(self, sources: list[str]):
        self.setting_component.source_a_combo["values"] = sources
        self.setting_component.source_b_combo["values"] = sources
        if sources and self.setting_component.source_a_var.get() not in sources:
            self.setting_component.source_a_var.set(sources[0])
        if sources and self.setting_component.source_b_var.get() not in sources:
            self.setting_component.source_b_var.set(sources[0])

    def set_queue_state(self, state: dict):
        import_queue = state.get("import_queue", []) or []
        play_queue = state.get("play_queue", []) or []
        self.playlist_component.set_queues(import_queue, play_queue)
        runner_running = bool(state.get("runner_running"))
        self.playlist_component.runner_status_var.set("Running" if runner_running else "Stopped")
        slot_a = state.get("slot_a_file", "")
        slot_b = state.get("slot_b_file", "")
        slot_a_name = slot_a.replace("\\", "/").split("/")[-1] if slot_a else "-"
        slot_b_name = slot_b.replace("\\", "/").split("/")[-1] if slot_b else "-"
        self.playlist_component.now_a_var.set(f"VideoA: {slot_a_name}")
        self.playlist_component.now_b_var.set(f"VideoB: {slot_b_name}")

    def get_selected_video_id(self) -> str:
        return self.playlist_component.selected_video_id()

    def set_selected_video_id(self, video_id: str):
        self.playlist_component.set_selected_video_id(video_id)
