version 1.0

# Check if array of files are tab-delimited
# Input type: Array of GZ files or files

task check_tab_delimited_array {
	input {
		Array[File] current_run_output
		Array[File] validated_output
	}

	Int disk_size = ceil((size(current_run_output[0], "GB") * length(current_run_output)) + (size(validated_output[0], "GB") * length(validated_output)) + 50)

	command <<<
		set -euo pipefail

		err() {
			message=$1

			echo -e "[ERROR] $message" >&2
		}

		# unzip every file in the input and output arrays
		if gzip -t ~{current_run_output[0]}; then
			while read -r file || [[ -n "$file" ]]; do
				gzip -d "$file"
			done < ~{write_lines(current_run_output)}

			while read -r file || [[ -n "$file" ]]; do
				gzip -d "$file"
			done < ~{write_lines(validated_output)}
		fi

		validated_dir_path=$(dirname ~{validated_output[0]})
		current_dir_path=$(dirname ~{current_run_output[0]})

		# Select tab-delimited files only
		tab_delimited_list=$(find "$validated_dir_path" -name "*.bed" -or -name "*.txt" -or -name "*.tsv" -or -name "*.ped" -or -name "*.gtf" -or -name "*.blocklist" -or -name "*.report" -type f)

		# This is the path/to/file string with separated file names by space
		file_names=$(for file in $tab_delimited_list; do
				basename "$file" .gz
			done)

		# Prepend appropriate path to each unzipped file
		# shellcheck disable=SC2001
		echo "$file_names" | sed "s;^;$validated_dir_path/;" > validated_tab_delimited_files.txt
		# shellcheck disable=SC2001
		echo "$file_names" | sed "s;^;$current_dir_path/;" > current_tab_delimited_files.txt

		while read -r file || [[ -n "$file" ]]; do
			if ! awk '{exit !/\t/}' "$file"; then
				err "Validated file: [$(basename "$file")] is not tab-delimited"
				exit 1
			fi
		done < validated_tab_delimited_files.txt

		while read -r file || [[ -n "$file" ]]; do
			if awk '{exit !/\t/}' "$file"; then
				echo "Current run file: [$(basename "$file")] is tab-delimited"
			else
				err "Current run file: [$(basename "$file")] is not tab-delimited"
				exit 1
			fi
		done < current_tab_delimited_files.txt
	>>>

	output {
	}

	runtime {
		docker: "ubuntu:xenial"
		cpu: 1
		memory: "3.75 GB"
		disk: disk_size + " GB"
		disks: "local-disk " + disk_size + " HDD"
		preemptible: 1
	}
}
