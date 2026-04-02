"""Low-level OBS websocket client adapter."""


def _safe_get(data, *keys, default=None):
    for key in keys:
        if isinstance(data, dict) and key in data:
            return data.get(key)
        if hasattr(data, key):
            return getattr(data, key)
    return default


class OBSWebSocketClient:
    """Thin wrapper over obsws_python ReqClient."""

    def __init__(self):
        self._client = None

    @property
    def connected(self) -> bool:
        return self._client is not None

    def connect(self, host: str, port: int, password: str, timeout: int = 3) -> dict:
        try:
            import obsws_python as obs
        except Exception as ex:
            raise RuntimeError(f"Thiếu package obsws-python: {ex}") from ex

        self._client = obs.ReqClient(host=host, port=port, password=password, timeout=timeout)
        version = self._client.get_version()
        return {
            "obs_version": getattr(version, "obs_version", "unknown"),
            "rpc_version": getattr(version, "rpc_version", "unknown"),
        }

    def disconnect(self):
        self._client = None

    def list_scenes(self) -> list[str]:
        if self._client is None:
            raise RuntimeError("OBS chưa connect")
        resp = self._client.get_scene_list()
        scenes = getattr(resp, "scenes", []) or []
        names = []
        for item in scenes:
            if isinstance(item, dict):
                names.append(str(item.get("sceneName", "")))
            else:
                names.append(str(getattr(item, "sceneName", "")))
        return [n for n in names if n]

    def list_sources(self, scene_name: str) -> list[str]:
        if self._client is None:
            raise RuntimeError("OBS chưa connect")
        resp = self._client.get_scene_item_list(scene_name)
        items = getattr(resp, "scene_items", []) or []
        names = []
        for item in items:
            if isinstance(item, dict):
                names.append(str(item.get("sourceName", "")))
            else:
                names.append(str(getattr(item, "sourceName", "")))
        return [n for n in names if n]

    def set_current_scene(self, scene_name: str):
        if self._client is None:
            raise RuntimeError("OBS chưa connect")
        self._client.set_current_program_scene(scene_name)

    def set_source_visibility(self, scene_name: str, source_name: str, visible: bool):
        if self._client is None:
            raise RuntimeError("OBS chưa connect")
        resp = self._client.get_scene_item_list(scene_name)
        items = getattr(resp, "scene_items", []) or []
        scene_item_id = None
        for item in items:
            name = _safe_get(item, "sourceName", "source_name", default="")
            if str(name) == source_name:
                scene_item_id = _safe_get(item, "sceneItemId", "scene_item_id")
                break
        if scene_item_id is None:
            raise RuntimeError(f"Không tìm thấy source '{source_name}' trong scene '{scene_name}'")
        self._client.set_scene_item_enabled(scene_name, int(scene_item_id), bool(visible))

    def set_media_local_file(self, input_name: str, file_path: str):
        if self._client is None:
            raise RuntimeError("OBS chưa connect")
        self._client.set_input_settings(input_name, {"local_file": file_path}, True)

    def restart_media(self, input_name: str):
        if self._client is None:
            raise RuntimeError("OBS chưa connect")
        self._client.trigger_media_input_action(input_name, "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART")

    def play_media(self, input_name: str):
        if self._client is None:
            raise RuntimeError("OBS chưa connect")
        self._client.trigger_media_input_action(input_name, "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PLAY")

    def get_media_status(self, input_name: str) -> dict:
        if self._client is None:
            raise RuntimeError("OBS chưa connect")
        resp = self._client.get_media_input_status(input_name)
        state = _safe_get(resp, "media_state", "mediaState", default="")
        duration = _safe_get(resp, "media_duration", "mediaDuration", default=0)
        cursor = _safe_get(resp, "media_cursor", "mediaCursor", default=0)
        return {
            "state": str(state or ""),
            "duration": int(duration or 0),
            "cursor": int(cursor or 0),
        }
