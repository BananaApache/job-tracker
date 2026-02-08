from api.models import JobEmail, Label, User


def wipe_emails_for_user(user: User):
    count, _ = JobEmail.objects.filter(user=user).delete()
    return count


def populate_email_database(user: User, parsed_emails):
    stats = {"created": 0, "updated": 0}

    for email_data in parsed_emails:
        label_names = email_data.pop("labels", [])

        email_obj, created = JobEmail.objects.update_or_create(
            gmail_id=email_data["gmail_id"], user=user, defaults=email_data
        )

        if not created:
            for key, value in email_data.items():
                if key != "gmail_id":
                    setattr(email_obj, key, value)
            email_obj.save()

        if label_names:
            label_objs = [Label.objects.get_or_create(name=name)[0] for name in label_names]
            email_obj.labels.set(label_objs)

        if created:
            stats["created"] += 1
        else:
            stats["updated"] += 1

    return stats
