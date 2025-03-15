# FXP2ADG Converter

A Python script converting VST FXP presets to Ableton Instrument Racks (ADG files).

## Description

This script allows to quickly **convert VST 2 plugin presets in FXP format to Ableton Instrument Racks (ADG files).**
It also **maps all preset macros to Instrument Rack macros (including macro names)**. This makes it much easier to load and control presets from Ableton Push level and gives easier access to plugin parameters in general (for example when using them with automation).

## Limitations

This script is experimental and has only been tested in some specific conditions. Having said that it should be possible to use it in other cases or configurations, but it's not guaranteed to work without some adjustments.

### Conditions used for testing
- Xfer Serum VST2 plugin
- macOS 15 Sequoia on M1 Pro
- Ableton Live 12.1.10 Suite
- a few preset packs from different authors

## System Requirements
- Python 3.12
- [uv](https://github.com/astral-sh/uv) for package management
- VST2 plugin matching the presets installed
- Ableton Live (to open the converted ADG files)

## Installation

Just clone the repository. `uv` will take care of creating `venv` and installing dependencies when running the script for the first time.

```bash
git clone https://github.com/mateuszkowalczyk/fxp2adg.git
```

## Usage

Run the script using `uv run` **inside** the project directory.

```bash
cd fxp2adg
uv run main.py <input_folder> <output_folder> [--plugin <plugin_path>]
```

Arguments:
- `input_folder`: Directory containing the FXP preset files
- `output_folder`: Directory where the converted ADG files will be saved
- `--plugin`: (Optional) Path to the VST plugin. Defaults to `/Library/Audio/Plug-Ins/VST/Serum.vst`

> [!NOTE]
> To use plugin other than Serum it is necessary to replace `template.adg` file inside the `data` directory. See [How It Works](#how-it-works) for details.

### Examples

Basic usage with default plugin path:

```bash
uv run main.py ./my_presets ./converted_presets
```

Specify a custom plugin path:

```bash
uv run main.py ./my_presets ./converted_presets --plugin "/Library/Audio/Plug-Ins/VST/MyPlugin.vst"
```

## How It Works

The conversion process works in the following steps:

1. **Loading the FXP preset**: The script loads the VST2 (I didn't manage to make it work with VST3 when reading parameters, although the output file works fine with VST3) plugin and loads preset data into it - it is necessary, because Serum (and most likely many other plugins) use their custom preset format that is difficult to read in other way.
2. **Extracting macro controls**: The script extracts macro controls including their values and names to use them to set Instrument Rack macros accordingly
3. **Creating the ADG file**:
   - The script loads a template Instrument Rack (ADG) file (which is a gzipped XML file). There is a Serum VST3 plugin inside the Instrument Rack with its macro parameters mapped to respective macros of Instrument Rack. It's necessary to replace the template file when using plugin different than Serum.
   - It decompresses the XML and modifies it to include the VST preset state and macro parameters
   - It recompresses the modified XML to create the final ADG file

## License

[MIT License](LICENSE.md)
