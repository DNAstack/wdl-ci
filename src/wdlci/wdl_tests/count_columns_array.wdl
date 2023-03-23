version 1.0

# Count columns
# Input type: Array of files

task count_columns_array {
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

		validated_output_column_count=$(while read -r file || [[ -n "$file" ]]; do
				awk '{print NF}' "$file" | sort -nu | tail -n 1
			done < ~{write_lines(validated_output)})

		current_run_output_column_count=$(while read -r file || [[ -n "$file" ]]; do
				awk '{print NF}' "$file" | sort -nu | tail -n 1
			done < ~{write_lines(current_run_output)})

		validated_output_column_count_string=$(echo "$validated_output_column_count" | tr '\n' ' ')
		current_run_output_column_count_string=$(echo "$current_run_output_column_count" | tr '\n' ' ')

		# Make it into an array
		validated_output_column_count_array=( "$validated_output_column_count_string" )
		current_run_output_column_count_array=( "$current_run_output_column_count_string" )

		# Validated and current should have the same amount of files
		length_array=$(echo "${#validated_output_column_count_array[@]}")

		for (( i=0; i<length_array; i++ )); do
			if [[ "${validated_output_column_count_array[$i]}" != "${current_run_output_column_count_array[$i]}" ]]; then
				err "Number of columns did not match:
					Expected output for [$(sed -n "$i"p current_bed_files.txt)]: [${validated_output_column_count_array[$i]}]
					Current run output [$(sed -n "$i"p validated_bed_files.txt)]: [${current_run_output_column_count_array[$i]}]"
				exit 1
			else
				echo "Number of columns matched [${validated_output_column_count_array[$i]}]"
			fi
		done
	>>>

	output {
		#Int rc = read_int("rc")
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
