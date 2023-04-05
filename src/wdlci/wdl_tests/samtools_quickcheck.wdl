version 1.0

# Samtools quickcheck on input files
# Input type: SAM/BAM/CRAM

task samtools_quickcheck {
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

		warn() {
			message=$1

			echo -e "[WARNING] $message" >&2
		}

		if ! samtools quickcheck ~{validated_output}; then
			warn "Validated output: [~{basename(validated_output)}] did not pass first samtools quickcheck"
		fi

		if ! samtools quickcheck -u ~{validated_output}; then
			err "Validated output: [~{basename(validated_output)}] did not pass samtools quickcheck with unmapped input flag"
			exit 1
		else
			if ! samtools quickcheck ~{current_run_output}; then
				warn "Current run output: [~{basename(current_run_output)}] did not pass first samtools quickcheck"
				if ! samtools quickcheck -u ~{current_run_output}; then
					err "Current run output: [~{basename(current_run_output)}] did not pass samtools quickcheck with unmapped input flag"
					exit 1
				else 
					echo "Current run output: [~{basename(current_run_output)}] passed samtools quickcheck with unmapped input flag"
				fi
			else
				echo "Current run output: [~{basename(current_run_output)}] passed samtools quickcheck"
			fi
		fi
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
