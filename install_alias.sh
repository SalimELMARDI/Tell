#!/usr/bin/env bash
set -euo pipefail

cwd="$(pwd)"
script_path="${cwd}/tell.sh"

if [[ ! -f "${script_path}" ]]; then
    echo "Error: ${script_path} not found. Run this script from the directory containing tell.sh."
    exit 1
fi

if [[ -f "${HOME}/.zshrc" ]]; then
    rc_file="${HOME}/.zshrc"
    shell_name="zsh"
elif [[ -f "${HOME}/.bashrc" ]]; then
    rc_file="${HOME}/.bashrc"
    shell_name="bash"
else
    rc_file="${HOME}/.bashrc"
    shell_name="bash"
    touch "${rc_file}"
fi

printf -v escaped_path '%q' "${script_path}"
alias_line="alias tell=\"${escaped_path}\""

if grep -Fq "alias tell=" "${rc_file}"; then
    echo "Alias 'tell' already exists in ${rc_file}. No changes made."
    exit 0
fi

echo "${alias_line}" >> "${rc_file}"
chmod +x "${script_path}"

echo "Alias added to ${rc_file}."
echo "Run: source ~/.${shell_name}rc"
