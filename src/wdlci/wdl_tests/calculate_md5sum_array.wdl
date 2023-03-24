version 1.0

# Compare file md5sums
# Input type: Array of files

task calculate_md5sum_array {
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

		# Compare files
		echo "Comparing file md5sums"

		current_run_md5sums=$(while read -r file || [[ -n "$file" ]]; do
				md5sum "$file" | cut -d ' ' -f 1
			done < ~{write_lines(current_run_output)})

		validated_output_md5sums=$(while read -r file || [[ -n "$file" ]]; do
				md5sum "$file" | cut -d ' ' -f 1
			done < ~{write_lines(validated_output)})

		#validated_output_md5sums=$(for file in "${validated_output[@]}"; do
		#	md5sum "$file" | cut -d ' ' -f 1
		#done)

		validated_output_md5sum_string=$(echo "$validated_output_md5sums" | tr '\n' ' ')
		current_run_output_md5sum_string=$(echo "$current_run_md5sums" | tr '\n' ' ')

		# Make it into an array
		validated_output_md5sum_array=( "$validated_output_md5sum_string" )
		current_run_output_md5sum_array=( "$current_run_output_md5sum_string" )

		# Validated and current should have the same amount of files
		length_array=${#validated_output_md5sum_array[@]}

		for (( i=0; i<length_array; i++ )); do
			if [[ "${current_run_output_md5sum_array[$i]}" != "${validated_output_md5sum_array[$i]}" ]]; then
				err "File md5sums did not match:
					Expected md5sum: [${validated_output_md5sum_array[$i]}]
					Current run md5sum: [${current_run_output_md5sum_array[$i]}]"
				exit 1
			else
				echo "File md5sums matched: [${validated_output_md5sum_array[$i]}]"
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
