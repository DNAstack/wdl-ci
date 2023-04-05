version 1.0

# Samtools quickcheck on input files
# Input type: Array of SAM/BAM/CRAM

task samtools_quickcheck_array {
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

		warn() {
			message=$1

			echo -e "[WARNING] $message" >&2
		}

		while read -r file || [[ -n "$file" ]]; do
			if ! samtools quickcheck "$file"; then
				warn "Validated output: [$(basename "$file")] did not pass first samtools quickcheck"
			else
				if ! samtools quickcheck -u "$file"; then
					err "Validated output: [$(basename "$file")] did not pass samtools quickcheck with unmapped input flag"
					exit 1
				fi
			fi
		done < ~{write_lines(validated_output)}

		while read -r file || [[ -n "$file" ]]; do
			if ! samtools quickcheck "$file"; then
				warn "Current run output: [$(basename "$file")] did not pass first samtools quickcheck"
				if ! samtools quickcheck -u "$file"; then
					err "Current run output: [$(basename "$file")] did not pass samtools quickcheck with unmapped input flag"
					exit 1
				else 
					echo "Current run output: [$(basename "$file")] passed samtools quickcheck with unmapped input flag"
				fi
			else
				echo "Current run output: [$(basename "$file")] passed samtools quickcheck"
			fi
		done < ~{write_lines(current_run_output)}
	>>>

	output {
	}

	runtime {
		docker: "dnastack/dnastack-wdl-ci-tools:0.0.1"
		cpu: 1
		memory: "3.75 GB"
		disk: disk_size + " GB"
		disks: "local-disk " + disk_size + " HDD"
		preemptible: 1
	}
}
