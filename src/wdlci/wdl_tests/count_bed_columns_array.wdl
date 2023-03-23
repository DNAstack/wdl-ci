version 1.0

# Count bed columns in array of files
# Input type: Array of BED files or BED GZ files

task count_bed_columns_array {
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

		validated_dir_path=$(dirname ~{validated_output[0]})
		current_dir_path=$(dirname ~{current_run_output[0]})

		# Select BED files only; -regex works for full path only
		bed_list=$(find "$validated_dir_path" -name '*.bed')

		# This is the path/to/file string with separated file names by space
		file_names=$(for file in $bed_list; do
				basename "$file" .gz
			done)

		# Prepend appropriate path to each unzipped file
		# shellcheck disable=SC2001
		echo "$file_names" | sed "s;^;$validated_dir_path/;" > validated_bed_files.txt
		# shellcheck disable=SC2001
		echo "$file_names" | sed "s;^;$current_dir_path/;" > current_bed_files.txt

		# unzip every file in the input and output arrays
		if gzip -t ~{validated_output[0]}; then
			while read -r file || [[ -n "$file" ]]; do
				gzip -d "$file"
			done < ~{write_lines(validated_output)}
			# Assuming header does not start with chr...
			validated_output_column_count=$(while read -r file || [[ -n "$file" ]]; do
				sed '/^chr/!d' "$file" | awk '{print NF}' | sort -nu | tail -n 1
			done < validated_bed_files.txt)
		else
			validated_output_column_count=$(while read -r file || [[ -n "$file" ]]; do
				sed '/^chr/!d' "$file" | awk '{print NF}' | sort -nu | tail -n 1
			done < validated_bed_files.txt)
		fi

		if gzip -t ~{current_run_output[0]}; then
			while read -r file || [[ -n "$file" ]]; do
				gzip -d "${file}"
			done < ~{write_lines(current_run_output)}
			current_run_output_column_count=$(while read -r file || [[ -n "$file" ]]; do
				sed '/^chr/!d' "$file" | awk '{print NF}' | sort -nu | tail -n 1
			done < current_bed_files.txt)
		else
			current_run_output_column_count=$(while read -r file || [[ -n "$file" ]]; do
				sed '/^chr/!d' "$file" | awk '{print NF}' | sort -nu | tail -n 1
			done < current_bed_files.txt)
		fi

		validated_output_column_count_string=$(echo "$validated_output_column_count" | tr '\n' ' ')
		current_run_output_column_count_string=$(echo "$current_run_output_column_count" | tr '\n' ' ')

		# Make it into an array
		validated_output_column_count_array=( "$validated_output_column_count_string" )
		current_run_output_column_count_array=( "$current_run_output_column_count_string" )

		# Validated and current should have the same amount of files
		length_array=${#validated_output_column_count_array[@]}

		for (( i=0; i<length_array; i++ )); do
			if [[ "${validated_output_column_count_array[$i]}" != "${current_run_output_column_count_array[$i]}" ]]; then
				err "Number of columns did not match:
					Expected output for [$(sed -n "$i"p current_bed_files.txt)]: [${validated_output_column_count_array[$i]}]
					Current run output [$(sed -n "$i"p validated_bed_files.txt)]: [${current_run_output_column_count_array[$i]}]"
					if [[ "${current_run_output_column_count_array[$i]}" -lt 3 ]] && [[ "${current_run_output_column_count_array[$i]}" -gt 12 ]]; then
						err "Invalid number of columns for a bed-format file for [$(sed -n "$i"p validated_bed_files.txt)]"
					fi
				exit 1
			else
				echo "Number of columns matched [${validated_output_column_count_array[$i]}]"
			fi
		done
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
