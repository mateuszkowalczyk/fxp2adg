import os
from dataclasses import dataclass
from typing import List
from pathlib import Path
import xml.etree.ElementTree as ET
import gzip
import fxp
import dawdreamer


@dataclass
class Param:
    id: int
    name: str
    value: float


def convert_fxp_to_adg(fxp_preset_path: str, adg_result_folder_path: str, adg_xml_template_path: str, plugin_path: str):
    MACRO_PARAM_IDS = list(range(218, 222))

    preset_state = read_preset_state(fxp_preset_path)
    macro_params = read_macro_params(
        fxp_preset_path, plugin_path, MACRO_PARAM_IDS)

    xml = ET.parse(adg_xml_template_path)
    xml_root = xml.getroot()

    set_preset_state(xml_root, preset_state)
    set_macro_params(xml_root, macro_params)

    xml_data = ET.tostring(xml_root, encoding="utf-8", xml_declaration=True)
    adg_data = gzip.compress(xml_data)
    result_path = get_result_path(adg_result_folder_path, fxp_preset_path)

    with open(result_path, "wb") as result_file:
        result_file.write(adg_data)


def read_preset_state(fxp_preset_path: str) -> bytes:
    preset = fxp.FXP(fxp_preset_path)
    return preset.data


def read_macro_params(fxp_preset_path: str, plugin_path: str, param_ids: List[int]) -> List[Param]:
    daw_engine = dawdreamer.RenderEngine(44100, 128)  # type: ignore
    plugin = daw_engine.make_plugin_processor("plugin", plugin_path)
    plugin.load_preset(fxp_preset_path)

    return [get_param(plugin, id) for id in param_ids]


def get_param(plugin, id: int) -> Param:
    return Param(id, plugin.get_parameter_name(id), plugin.get_parameter(id))


def set_preset_state(xml_root, preset_state: bytes):
    hex_data = preset_state.hex().upper()

    processor_state_tag = xml_root.find('.//ProcessorState')
    if processor_state_tag is not None:
        processor_state_tag.text = hex_data


def set_macro_params(xml_root, macro_params: List[Param]):
    for i, param in enumerate(macro_params):
        value_string = float_to_macro_value_string(param.value)

        xml_root.find(
            f".//MacroControls.{i}/Manual").attrib['Value'] = value_string
        xml_root.find(f".//MacroDisplayNames.{i}").attrib['Value'] = param.name
        xml_root.find(f".//MacroDefaults.{i}").attrib['Value'] = value_string


def float_to_macro_value_string(float_value: float) -> str:
    MAX_MACRO_VALUE = 127
    macro_value = round(float_value * MAX_MACRO_VALUE)
    return str(macro_value)


def get_result_path(folder_path: str, preset_path: str) -> str:
    path = Path(preset_path)
    result_name = path.with_suffix(".adg").name
    return os.path.join(folder_path, result_name)


if __name__ == "__main__":
    convert_fxp_to_adg("FX Alien interface [SN].fxp", "",
                       "data/template.xml", "/Library/Audio/Plug-Ins/VST/Serum.vst")
