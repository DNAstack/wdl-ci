version 1.0

# Count bed columns
# Input type: BED file or BED GZ file

task count_bed_columns {
	input {
		File current_run_output
		File validated_output
	}

	Int disk_size = ceil(size(current_run_output, "GB") + size(validated_output, "GB") + 50)

	command <<<
		set -euo pipefail

		err() {
			message=$1

			echo -e "[ERROR] $message" >&2
		}

		# Validated dir path in input block vs. command block is different
		validated_dir_path=$(dirname ~{validated_output})
		current_dir_path=$(dirname ~{current_run_output})

		if gzip -tq ~{current_run_output}; then
			gzip -d -f ~{current_run_output} ~{validated_output}
			# Assuming header does not start with chr...
			current_run_output_column_count=$(sed '/^chr/!d' "${current_dir_path}/$(basename ~{current_run_output} .gz)" | awk '{print NF}' | sort -nu | tail -n 1)
			validated_output_column_count=$(sed '/^chr/!d' "${validated_dir_path}/$(basename ~{validated_output} .gz)" | awk '{print NF}' | sort -nu | tail -n 1)
		else
			current_run_output_column_count=$(sed '/^chr/!d' ~{current_run_output} | awk '{print NF}' | sort -nu | tail -n 1)
			validated_output_column_count=$(sed '/^chr/!d' ~{validated_output} | awk '{print NF}' | sort -nu | tail -n 1)
		fi

		if [[ "$current_run_output_column_count" != "$validated_output_column_count" ]]; then
			err "Number of columns did not match:
				Expected output: [$validated_output_column_count]
				Current run output: [$current_run_output_column_count]"
				if [[ "$current_run_output_column_count" -lt 3 ]] && [[ "$current_run_output_column_count" -gt 12 ]]; then
					err "Invalid number of columns for a bed-format file"
				fi
			exit 1
		else
			echo "Number of columns matched [$validated_output_column_count]"
		fi
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
