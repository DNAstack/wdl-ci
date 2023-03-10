version 1.0

# Count bed columns
# Input type: BED file

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

		if gzip -t ~{current_run_output}; then
			dir_path=$(dirname ~{current_run_output})
			gzip -d ~{current_run_output} ~{validated_output}
			current_run_output_column_count=$(awk '{print NF}' "${dir_path}/$(basename ~{current_run_output} .gz)" | sort -nu | tail -n 1)
			validated_output_column_count=$(awk '{print NF}' "${dir_path}/$(basename ~{validated_output} .gz)" | sort -nu | tail -n 1)
		else
			current_run_output_column_count=$(awk '{print NF}' ~{current_run_output} | sort -nu | tail -n 1)
			validated_output_column_count=$(awk '{print NF}' ~{validated_output} | sort -nu | tail -n 1)
		fi

		if [[ "$current_run_output_column_count" != "$validated_output_column_count" ]]; then
			err "Number of columns did not match:
				Expected output: [$validated_output_column_count]
				Current run output: [$current_run_output_column_count]"
				if [[ "$current_run_output_column_count" -lt 3 ]] && [[ "$current_run_output_column_count" -gt 12 ]]; then
					err "Invalid number of columns"
				fi
			exit 1
		else
			echo "Number of columns matched [$validated_output_column_count]"
		fi
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
