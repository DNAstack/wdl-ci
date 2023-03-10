version 1.0

# Count bed columns in array of files
# Input type: Array of BED files

task count_bed_columns_array {
	input {
		Array[File] current_run_output
		Array[File] validated_output
	}

	String first_current_run_output = current_run_output[0]
	String first_validated_output = validated_output[0]

	Int disk_size = ceil((size(current_run_output[0], "GB") * length(current_run_output)) + (size(validated_output[0], "GB") * length(validated_output)) + 50)
	
	command <<<
		set -euo pipefail

		err() {
			message=$1

			echo -e "[ERROR] $message" >&2
		}

		if gzip -t ~{first_validated_output}; then
			for file in ~{sep=' ' validated_output}; do 	
				gzip -d "${file}"
			done
			validated_output_column_count=$(for file in ~{sep=' ' validated_output}; do
				awk '{print NF}' "$(basename ${file} .gz)" | sort -nu | tail -n 1
			done)
		else
			validated_output_column_count=$(for file in ~{sep=' ' validated_output}; do
				awk '{print NF}' "${file}" | sort -nu | tail -n 1
			done)
		fi

		if gzip -t ~{first_current_run_output}; then
			for file in ~{sep=' ' current_run_output}; do 	
				gzip -d "${file}"
			done
			current_run_output_column_count=$(for file in ~{sep=' ' current_run_output}; do
				awk '{print NF}' "$(basename ${file} .gz)" | sort -nu | tail -n 1
			done)
		else
			current_run_output_column_count=$(for file in ~{sep=' ' current_run_output}; do
				awk '{print NF}' "${file}" | sort -nu | tail -n 1
			done)
		fi

		validated_output_column_count_array=$(echo "$validated_output_column_count" | tr '\n' ' ')
		current_run_output_column_count_array=$(echo "$current_run_output_column_count" | tr '\n' ' ')

		# Validated and current should have the same amount of files
		length_array=$("${#validated_output_column_count_array[@]}")

		for (( i=0; i<length_array; i++ )); do
			if [[ "${validated_output_column_count_array[$i]}" != "${current_run_output_column_count_array[$i]}" ]]; then
				err "Number of columns did not match:
					Expected output: [${validated_output_column_count_array[$i]}]
					Current run output: [${current_run_output_column_count_array[i]}]"
					if [[ "${current_run_output_column_count_array[$i]}" -lt 3 ]] && [[ "${current_run_output_column_count_array[$i]}" -gt 12 ]]; then
						err "Invalid number of columns"
					fi
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
