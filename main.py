import os
from dataclasses import dataclass
from typing import List
from pathlib import Path
import xml.etree.ElementTree as ET
import gzip
import fxp
import dawdreamer


FXP_EXTENSION = ".fxp"
ADG_EXTENSION = ".adg"
ADG_TEMPLATE_PATH = os.path.join("data", "template.adg")


@dataclass
class Param:
    param_id: int
    name: str
    value: float


def convert_fxp_in_folder_to_adg(
    fxp_folder_path: str,
    adg_result_folder_path: str,
    plugin_path: str,
):
    """
    Converts all FXP preset files in a folder to ADG format.

    Args:
        fxp_folder_path: Path to the folder containing FXP preset files
        adg_result_folder_path: Path to the folder where ADG files will be saved
        plugin_path: Path to the VST plugin

    Returns:
        None
    """

    if not Path(plugin_path).exists():
        raise FileNotFoundError(f"Plugin not found: {plugin_path}")

    folder_path = Path(fxp_folder_path)

    if not folder_path.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    os.makedirs(adg_result_folder_path, exist_ok=True)

    for file_path in folder_path.glob(f"*{FXP_EXTENSION}"):
        if file_path.is_file():
            convert_fxp_to_adg(
                str(file_path),
                adg_result_folder_path,
                ADG_TEMPLATE_PATH,
                plugin_path,
            )


def convert_fxp_to_adg(
    fxp_preset_path: str,
    adg_result_folder_path: str,
    adg_template_path: str,
    plugin_path: str,
):
    """
    Converts a FXP preset to an ADG preset.

    Args:
        fxp_preset_path: Path to the FXP preset file.
        adg_result_folder_path: Path to the folder where the ADG preset will be saved.
        adg_template_path: Path to the ADG template file.
        plugin_path: Path to the plugin file.

    Returns:
        None
    """

    macro_param_ids = list(range(218, 222))

    preset_state = _read_preset_state(fxp_preset_path)
    macro_params = _read_macro_params(fxp_preset_path, plugin_path, macro_param_ids)

    xml = _load_template_xml(adg_template_path)

    _set_preset_state(xml, preset_state)
    _set_macro_params(xml, macro_params)

    xml_data = ET.tostring(xml, encoding="utf-8", xml_declaration=True)
    adg_data = gzip.compress(xml_data)

    result_path = _get_result_path(adg_result_folder_path, fxp_preset_path)

    with open(result_path, "wb") as result_file:
        result_file.write(adg_data)


def _read_preset_state(fxp_preset_path: str) -> bytes:
    preset = fxp.FXP(fxp_preset_path)
    return preset.data


def _read_macro_params(
    fxp_preset_path: str, plugin_path: str, param_ids: List[int]
) -> List[Param]:
    daw_engine = dawdreamer.RenderEngine(44100, 128)
    plugin = daw_engine.make_plugin_processor("plugin", plugin_path)
    plugin.load_preset(fxp_preset_path)
    return [_get_param(plugin, param_id) for param_id in param_ids]


def _load_template_xml(adg_template_path: str) -> ET.Element:
    with open(adg_template_path, "rb") as template:
        template_data = template.read()

    xml_data = gzip.decompress(template_data)
    return ET.fromstring(xml_data)


def _get_param(plugin, param_id: int) -> Param:
    return Param(
        param_id, plugin.get_parameter_name(param_id), plugin.get_parameter(param_id)
    )


def _set_preset_state(xml_root, preset_state: bytes):
    hex_data = preset_state.hex().upper()

    processor_state_tag = xml_root.find(".//ProcessorState")
    if processor_state_tag is not None:
        processor_state_tag.text = hex_data


def _set_macro_params(xml_root, macro_params: List[Param]):
    for i, param in enumerate(macro_params):
        value_string = _float_to_macro_value_string(param.value)

        xml_root.find(f".//MacroControls.{i}/Manual").attrib["Value"] = value_string
        xml_root.find(f".//MacroDisplayNames.{i}").attrib["Value"] = param.name
        xml_root.find(f".//MacroDefaults.{i}").attrib["Value"] = value_string


def _float_to_macro_value_string(float_value: float) -> str:
    MAX_MACRO_VALUE = 127
    macro_value = round(float_value * MAX_MACRO_VALUE)
    return str(macro_value)


def _get_result_path(folder_path: str, preset_path: str) -> str:
    path = Path(preset_path)
    result_name = path.with_suffix(ADG_EXTENSION).name
    return os.path.join(folder_path, result_name)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Convert FXP presets to ADG format')
    parser.add_argument('input', help='Folder containing FXP preset files')
    parser.add_argument('output', help='Folder where converted ADG files will be save')
    parser.add_argument('--plugin', default="/Library/Audio/Plug-Ins/VST/Serum.vst", help='Path to VST plugin')

    args = parser.parse_args()

    try:
        convert_fxp_in_folder_to_adg(
            args.input, args.output, args.plugin
        )
    except FileNotFoundError as e:
        print(e)
