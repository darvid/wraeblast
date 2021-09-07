#!/bin/bash
league="$(<.current_league)"
filters_prefix=./filters

main() {
  local filter_options=( "$@" )
  if [[ ${#filter_options} -eq 0 ]] || [[ "${filter_options[0]}" == "ALL" ]]; then
    readarray filter_options < <("${filters_prefix}"/list.sh)
    echo "${#filter_options[@]}"
  fi
  for config_file in "${filter_options[@]}"; do
    filter_dirname="$(dirname "${config_file}")"
    filter_basename="$(basename "$filter_dirname")"
    options_basename="$(basename "${config_file}")"
    options_name="${options_basename%*.config.json}"
    echo "building ${options_name}..."
    wraeblast render_filter \
      --league "${league}" \
      --preset endgame \
      --keep-intermediate \
      --no-sync \
      --output-directory output/"${filter_basename}" \
      --options-file "$config_file" \
      --output "WB-${league}-${options_name}.filter" \
      "${filters_prefix}"/"${filter_basename}"/"${filter_basename}.yaml.j2"
  done
}

main "$@"
