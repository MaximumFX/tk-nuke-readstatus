[![Code style: autopep8](https://img.shields.io/badge/code%20style-autopep8-000000.svg)](https://github.com/psf/black)
![GitHub release (latest by date including pre-releases)](https://img.shields.io/github/v/release/maximumfx/tk-nuke-readstatus?include_prereleases)
[![GitHub issues](https://img.shields.io/github/issues/maximumfx/tk-nuke-readstatus)](https://github.com/maximumfx/tk-nuke-readstatus/issues)
# tk-nuke-readstatus

`tk-nuke-readstatus` is a Shotgun Toolkit app which adds status indicators to read nodes.

## Installation

Todo

## Configuration

| Type     | Key                      | Description                                                                          | Default value                       |
|----------|--------------------------|--------------------------------------------------------------------------------------|-------------------------------------|
| str      | `oiiotool`               | Path to oiiotool binary. If blank, the hoiiotool included with Houdini will be used. |                                     |

### Example configuration
```yaml
settings.tk-nuke-readstatus:
  question_on_missing: true
  missing_icon:
    name: out_of_pipe
    scale: 0.5
    offsetX: 84
    offsetY: 0
    
  icon_base_path: icons/tk-nuke-readstatus
  
  statuses:
    # Asset
    - icon:
        name: asset
        scale: 0.5
        offsetX: 84
        offsetY: 0
      match_both: false
      str_include:
        - X:\
      template_match: []
      latest: false

  versionable:
    - nuke_asset_render
    - nuke_asset_render_pub
    - houdini_asset_render

  work_publish_mappings:
    - work: nuke_asset_render
      publish: nuke_asset_render_pub
```

## License

[MIT](https://choosealicense.com/licenses/mit/)
