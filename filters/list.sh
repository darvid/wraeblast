#!/bin/bash
main() {
  local filter_path="${1:-./filters}"
  local chunk_size="${2:-0}"
  local filter_options=()
  local dir_options=()
  for dir in "${filter_path}"/*/; do
    dir_name="$(basename $dir)"
    readarray -d '' dir_options < <(find "$dir" -name "*.config.json" -print0 | sort -z)
    filter_options=( "${filter_options[@]}" "${dir_options[@]}" )
  done

  if (( $chunk_size > 0 )); then
    for ((i=0; i < ${#filter_options[@]}; i+=chunk_size)); do
      local chunk=( "${filter_options[@]:i:chunk_size}" )
      echo "${chunk[@]}"
    done
  else
    printf "%s\n" "${filter_options[@]}"
  fi
}

main "$@"
