version 1.0

# Compare md5sums of SAM records in input files, e.g., BAMs or CRAMs while ignoring headers
# Input type: SAM/BAM/CRAM

task calculate_sam_record_md5sum {
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

		# Compare files
		echo "Comparing SAM record md5sums"
		current_run_md5sum=$(samtools view ~{current_run_output} | md5sum | cut -d ' ' -f 1)
		validated_output_md5sum=$(samtools view ~{validated_output} | md5sum | cut -d ' ' -f 1)

		if [[ "$current_run_md5sum" != "$validated_output_md5sum" ]]; then
			err "SAM record md5sums did not match:
				Expected md5sum: [$validated_output_md5sum]
				Current run md5sum: [$current_run_md5sum]"
			exit 1
		else
			echo "SAM record md5sums matched for file [~{basename(validated_output)}]"
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
