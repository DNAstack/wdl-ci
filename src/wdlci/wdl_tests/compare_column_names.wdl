version 1.0

# Compare column names in metadata
# Input type: File

task compare_column_names {
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

		current_run_header=$(head -1 ~{current_run_output})
		validated_header=$(head -1 ~{validated_output})

		if [[ "$current_run_header" != "$validated_header" ]]; then
			err "Check 1/2:
				Headers did not match:
				Expected header:
				$current_run_header
				Validated header:
				$validated_header"
			exit 1
		else
			echo "Headers matched:"
			echo "$validated_header"
		fi

		current_run_header_sorted=$(echo "$current_run_header" | xargs -n1 | sort | xargs)
		validated_header_sorted=$(echo "$validated_header" | xargs -n1 | sort | xargs)

		if [[ "$current_run_header_sorted" != "$validated_header_sorted" ]]; then
			err "Check 2/2:
				Sorted headers did not match:
				Sorted expected header:
				$current_run_header_sorted
				Sorted validated header:
				$validated_header_sorted"
			exit 1
		else
			echo "Sorted headers matched:"
			echo "$validated_header_sorted"
		fi
	>>>

	output {
		Int rc = read_int("rc")
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
