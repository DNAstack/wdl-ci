version 1.0

# Check empty lines
# Input type: Array of files or GZ files

task check_empty_lines_array {
	input {
		Array[File] current_run_output
		Array[File] validated_output
	}

	Int disk_size = ceil(size(current_run_output, "GB") + size(validated_output, "GB") + 50)

	command <<<
		set -euo pipefail

		err() {
			message=$1

			echo -e "[ERROR] $message" >&2
		}

		if gzip -t ~{current_run_output[0]}; then
			current_run_output_empty_lines_count=$(zgrep -c "^$" ~{sep=' ' current_run_output} || [[ $? == 1 ]])
			validated_output_empty_lines_count=$(zgrep -c "^$" ~{sep=' ' validated_output} || [[ $? == 1 ]])
		else
			current_run_output_empty_lines_count=$(grep -c "^$" ~{sep=' ' current_run_output} || [[ $? == 1 ]])
			validated_output_empty_lines_count=$(grep -c "^$" ~{sep=' ' validated_output} || [[ $? == 1 ]])
		fi

		# This is a variable with empty line count by space
		current_run_output_empty_lines_counts=$(for count in $current_run_output_empty_lines_count; do
				echo "${count/*:/}"
			done)
		validated_output_empty_lines_counts=$(for count in $validated_output_empty_lines_count; do
				echo "${count/*:/}"
			done)

		# Make it into an array
		mapfile -t current_run_output_empty_lines_counts_array < <(echo "$current_run_output_empty_lines_counts" | tr ' ' '\n')
		mapfile -t validated_output_empty_lines_counts_array < <(echo "$validated_output_empty_lines_counts" | tr ' ' '\n')

		# Validated and current should have the same amount of files
		length_array=${#validated_output_empty_lines_counts_array[@]}

		for (( i=0; i<length_array; i++ )); do
			if [[ "${validated_output_empty_lines_counts_array[$i]}" != 0 ]]; then
				err "Empty lines present in validated output. Count: [${validated_output_empty_lines_counts_array[$i]}]"
				exit 1
			fi
		done

		for (( i=0; i<length_array; i++ )); do
			if [[ "${validated_output_empty_lines_counts_array[$i]}" != "${current_run_output_empty_lines_counts_array[$i]}" ]]; then
				err "Empty lines present:
					Expected output: [${validated_output_empty_lines_counts_array[$i]}]
					Current run output: [${current_run_output_empty_lines_counts_array[$i]}]"
				exit 1
			else
				echo "No empty lines. Count: [${validated_output_empty_lines_counts_array[$i]}]"
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
