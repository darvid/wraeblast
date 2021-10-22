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
    extra_args=()
    if [[ "$filter_basename" == "leaguestart" ]]; then
      extra_args+=( --no-insights )
      preset="default"
    else
      preset="endgame"
    fi
    wraeblast render_filter \
      --league "${league}" \
      --preset "$preset" \
      --keep-intermediate \
      --no-sync \
      --output-directory output/"${filter_basename}" \
      --options-file "$config_file" \
      --output "WB-{league_short}-${options_name}.filter" \
      "${extra_args[@]}" \
      "${filters_prefix}"/"${filter_basename}"/"${filter_basename}.yaml.j2"
  done
}

main "$@"
