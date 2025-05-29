version 1.0

# Count columns
# Input type: File

task count_columns {
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

		current=~{current_run_output}
		validated=~{validated_output}

		if gzip -t ~{current_run_output} 2> /dev/null; then
			gzip -d -f ~{current_run_output} ~{validated_output}
			current=$(dirname ~{current_run_output})/$(basename ~{current_run_output} .gz)
			validated=$(dirname ~{validated_output})/$(basename ~{validated_output} .gz)
		fi

		if echo "$current" | grep ".csv$"; then
			current_run_output_column_count=$(sed 's;,;\t;g' "$current" | awk '{print NF}' | sort -nu | tail -n 1)
			validated_output_column_count=$(sed 's;,;\t;g' "$validated" | awk '{print NF}' | sort -nu | tail -n 1)
		else
			# Disregard headers starting with `#`
			current_run_output_column_count=$(sed '/^#/d' "$current" | awk '{print NF}' | sort -nu | tail -n 1)
			validated_output_column_count=$(sed '/^#/d' "$validated" | awk '{print NF}' | sort -nu | tail -n 1)
		fi

		if [[ "$current_run_output_column_count" != "$validated_output_column_count" ]]; then
			err "Number of columns did not match:
				Expected output: [$validated_output_column_count]
				Current run output: [$current_run_output_column_count]"
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
