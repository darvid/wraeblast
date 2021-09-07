#!/bin/bash
league="$(<.current_league)"

main() {
  local filter_path="${1:-./filters}"
  for dir in "${filter_path}"/*/; do
    dir_name="$(basename $dir)"
    echo "$dir_name"
    echo "processing $dir..."
    local templates=("${dir}/"*.config.json)
    for cfg_file in "${templates[@]}"; do
      filter_basename="$(basename "$cfg_file")"
      filter_name="${filter_basename%*.config.json}"
      echo "building ${filter_name}..."
      wraeblast render_filter \
        -l "${league}" \
        -p endgame -i \
        -d output/"${dir_name}" \
        -O "$cfg_file" \
        -o "WB-${league}-${filter_name}.filter" \
        "${dir}"/"${dir_name}.yaml.j2"
    done
  done
}

main "$@"
