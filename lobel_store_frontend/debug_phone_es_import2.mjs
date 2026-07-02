import phone from 'react-phone-input-2';
console.log('phone keys', Object.keys(phone));
console.log('phone default exists', phone.default !== undefined);
if (phone.default) {
  console.log('phone.default type', typeof phone.default);
  console.log('phone.default $$typeof', phone.default.$$typeof);
  console.log('phone.default name', phone.default.name);
}
